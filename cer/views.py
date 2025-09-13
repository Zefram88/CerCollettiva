# cer/views.py
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.main_models import CERConfiguration, CERMembership, Plant
from users.models import CustomUser

from .forms import (
    OnboardingStep1Form,
    OnboardingStep2Form,
    OnboardingStep3Form,
    OnboardingStep4Form,
    OnboardingStep5Form,
    ProfileCompletionForm,
)
from .models import MemberProfile

# from django.views.decorators.http import require_http_methods  # Unused



logger = logging.getLogger(__name__)


@login_required
def onboarding_wizard(request):
    """Wizard configurazione socio CER - Entry point"""
    user = request.user

    # Verifica che l'utente sia nel giusto stato
    if user.onboarding_status != CustomUser.OnboardingStatus.ANAGRAFICA_COMPLETA:
        messages.warning(request, _("Devi completare prima il profilo anagrafico."))
        return redirect("users:profile_complete")

    # Verifica che esista un profilo membro
    try:
        member_profile = user.member_profile
    except MemberProfile.DoesNotExist:
        messages.error(
            request, _("Profilo membro non trovato. Contatta l'amministratore.")
        )
        return redirect("core:dashboard")

    # Verifica che il profilo sia completo
    if not member_profile.is_complete:
        messages.warning(
            request, _("Completa prima tutti i campi del profilo anagrafico.")
        )
        return redirect("users:profile_complete")

    # Redirect al primo step
    return redirect("cer:onboarding_step", step=1)


@login_required
def onboarding_step(request, step):
    """Gestisce i singoli step del wizard"""
    user = request.user

    # Verifica stato utente
    if user.onboarding_status != CustomUser.OnboardingStatus.ANAGRAFICA_COMPLETA:
        messages.warning(request, _("Devi completare prima il profilo anagrafico."))
        return redirect("users:profile_complete")

    # Verifica step valido
    if step not in range(1, 6):
        messages.error(request, _("Step non valido."))
        return redirect("cer:onboarding_wizard")

    # Ottieni il profilo membro
    try:
        member_profile = user.member_profile
    except MemberProfile.DoesNotExist:
        messages.error(request, _("Profilo membro non trovato."))
        return redirect("core:dashboard")

    # Gestisci POST per ogni step
    if request.method == "POST":
        return _handle_step_post(request, step, member_profile)

    # Gestisci GET per ogni step
    return _handle_step_get(request, step, member_profile)


def _handle_step_get(request, step, member_profile):
    """Gestisce le richieste GET per ogni step"""
    forms_map = {
        1: OnboardingStep1Form,
        2: OnboardingStep2Form,
        3: OnboardingStep3Form,
        4: OnboardingStep4Form,
        5: OnboardingStep5Form,
    }

    form_class = forms_map[step]
    form = form_class()

    # Pre-popola il form con dati esistenti se disponibili
    if hasattr(member_profile, "onboarding_data"):
        form = form_class(
            initial=member_profile.onboarding_data.get(f"step_{step}", {})
        )

    context = {
        "step": step,
        "total_steps": 5,
        "form": form,
        "member_profile": member_profile,
        "progress_percentage": (step / 5) * 100,
    }

    return render(request, f"cer/onboarding/step{step}.html", context)


def _handle_step_post(request, step, member_profile):
    """Gestisce le richieste POST per ogni step"""
    forms_map = {
        1: OnboardingStep1Form,
        2: OnboardingStep2Form,
        3: OnboardingStep3Form,
        4: OnboardingStep4Form,
        5: OnboardingStep5Form,
    }

    form_class = forms_map[step]
    form = form_class(request.POST, request.FILES)

    if form.is_valid():
        # Salva i dati dello step
        _save_step_data(member_profile, step, form.cleaned_data)

        # Logica speciale per Step 2 (POD)
        if step == 2:
            # Aggiungi automaticamente la CER unica se non specificata
            step_data = member_profile.onboarding_data.get("step_2", {})
            if not step_data.get("cer_configuration") and not step_data.get(
                "create_new_cer"
            ):
                cer_config = CERConfiguration.objects.filter(is_active=True).first()
                if cer_config:
                    step_data["cer_configuration"] = cer_config.id
                    member_profile.onboarding_data["step_2"] = step_data
                    member_profile.save()

        # Gestisci navigazione
        if "next" in request.POST:
            if step == 2:
                # Dopo lo Step 2 (POD), completa l'onboarding
                return _complete_onboarding(request, member_profile)
            elif step < 5:
                return redirect("cer:onboarding_step", step=step + 1)
            else:
                # Ultimo step - completa l'onboarding
                return _complete_onboarding(request, member_profile)
        elif "previous" in request.POST and step > 1:
            return redirect("cer:onboarding_step", step=step - 1)
        else:
            # Salva e continua dopo
            return redirect("cer:onboarding_wizard")
    else:
        # Form non valido, mostra errori
        pass

    # Se il form non è valido, mostra gli errori
    context = {
        "step": step,
        "total_steps": 5,
        "form": form,
        "member_profile": member_profile,
        "progress_percentage": (step / 5) * 100,
    }

    return render(request, f"cer/onboarding/step{step}.html", context)


def _save_step_data(member_profile, step, data):
    """Salva i dati di uno step nel profilo membro"""
    if not hasattr(member_profile, "onboarding_data"):
        member_profile.onboarding_data = {}

    # Step 2: Risolvi POD e aggiorna dati
    if step == 2 and "pod_code" in data:
        try:
            from .pod_resolver import GSEPodResolver

            with GSEPodResolver() as resolver:
                pod_result = resolver.resolve_pod(data["pod_code"])
                data["pod_info"] = {
                    "cabina_primaria": pod_result.cabina_primaria,
                    "fornitore": pod_result.fornitore,
                    "regioni": pod_result.regioni,
                    "province": pod_result.province,
                    "comuni": pod_result.comuni,
                }
        except Exception as e:
            # Se la risoluzione fallisce, continua senza i dati aggiuntivi
            logger.warning(f"Errore nella risoluzione POD {data['pod_code']}: {e}")

    # Converti oggetti date in stringhe per la serializzazione JSON
    serializable_data = {}
    for key, value in data.items():
        if hasattr(value, "isoformat"):  # date, datetime objects
            serializable_data[key] = value.isoformat()
        else:
            serializable_data[key] = value

    member_profile.onboarding_data[f"step_{step}"] = serializable_data
    member_profile.save()


@transaction.atomic
def _complete_onboarding(request, member_profile):
    """Completa il processo di onboarding creando la membership CER"""
    user = request.user

    try:
        # Ottieni i dati del POD
        pod_data = member_profile.onboarding_data.get("step_2", {})
        create_new_cer = pod_data.get("create_new_cer")
        cer_config_id = pod_data.get("cer_configuration")

        # Gestisci creazione nuova CER o selezione esistente
        if create_new_cer:
            # Crea una nuova CER
            cer_config = _create_new_cer(request, pod_data, user)
            if not cer_config:
                return redirect("cer:onboarding_step", step=2)
        else:
            # Usa CER esistente - se non specificata, usa la CER unica attiva
            if cer_config_id:
                cer_config = get_object_or_404(
                    CERConfiguration, id=cer_config_id, is_active=True
                )
            else:
                # CER unica automatica
                cer_config = CERConfiguration.objects.filter(is_active=True).first()
                if not cer_config:
                    messages.error(
                        request,
                        _("Nessuna CER attiva disponibile. Contatta l'amministratore."),
                    )
                    return redirect("cer:onboarding_step", step=2)

        # Crea la membership CER
        membership_data = member_profile.onboarding_data.get("step_1", {})
        CERMembership.objects.create(
            user=user,
            cer_configuration=cer_config,
            role="MEMBER",
            member_type=membership_data.get("member_type", "CONSUMER"),
            is_active=True,
            joined_date=timezone.now().date(),
        )

        # Se l'utente ha un impianto, crealo
        plant_data = member_profile.onboarding_data.get("step_3", {})
        if plant_data.get("has_plant"):
            Plant.objects.create(
                name=f"Impianto {user.get_full_name()}",
                owner=user,
                pod_code=pod_data.get("pod_code", ""),
                plant_type="PHOTOVOLTAIC",
                nominal_power=plant_data.get("plant_power", 0),
                installation_date=plant_data.get("plant_installation_date"),
                address=pod_data.get("pod_address", ""),
                is_active=True,
                cer_configuration=cer_config,
            )

        # Aggiorna lo stato di onboarding
        user.onboarding_status = CustomUser.OnboardingStatus.ONBOARDING_COMPLETATO
        user.save()

        # Pulisci i dati temporanei del wizard
        member_profile.onboarding_data = {}
        member_profile.save()

        messages.success(
            request, _("Onboarding completato con successo! Benvenuto nella CER.")
        )
        return redirect("core:dashboard")

    except Exception as e:
        logger.error(f"Errore nel completamento onboarding per utente {user.id}: {e}")
        messages.error(
            request, _("Errore durante il completamento dell'onboarding. Riprova.")
        )
        return redirect("cer:onboarding_wizard")


def _create_new_cer(request, pod_data, user):
    """Crea una nuova CER basata sui dati del POD"""
    try:
        new_cer_name = pod_data.get("new_cer_name")
        new_cer_description = pod_data.get("new_cer_description", "")

        if not new_cer_name:
            messages.error(request, _("Nome della nuova CER richiesto."))
            return None

        # Genera un codice CER univoco
        import uuid

        cer_code = f"CER_{uuid.uuid4().hex[:8].upper()}"

        # Ottieni informazioni dal POD per la localizzazione
        # pod_info = pod_data.get("pod_info", {})  # Unused
        # regioni = pod_info.get("regioni", [])  # Unused
        # province = pod_info.get("province", [])  # Unused

        # Crea la nuova CER
        cer_config = CERConfiguration.objects.create(
            name=new_cer_name,
            code=cer_code,
            description=new_cer_description
            or f"Comunità Energetica Rinnovabile creata da {user.get_full_name()}",
            primary_substation=pod_data.get("pod_code", ""),
            is_active=True,
            # Qui potresti aggiungere altri campi basati sui dati del POD
        )

        logger.info(
            f"Nuova CER creata: {cer_config.name} (ID: {cer_config.id}) "
            f"da utente {user.id}"
        )
        messages.success(request, _("Nuova CER creata con successo!"))

        return cer_config

    except Exception as e:
        logger.error(f"Errore nella creazione CER per utente {user.id}: {e}")
        messages.error(request, _("Errore nella creazione della nuova CER. Riprova."))
        return None


@login_required
def resolve_pod(request):
    """API per risolvere un POD e ottenere informazioni CER disponibili"""
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Metodo non supportato"}, status=405
        )

    pod_code = request.POST.get("pod_code", "").strip().upper()
    if not pod_code:
        return JsonResponse(
            {"status": "error", "message": "Codice POD richiesto"}, status=400
        )

    try:
        from .pod_resolver import GSEPodResolver

        with GSEPodResolver() as resolver:
            pod_result = resolver.resolve_pod(pod_code)

            # Trova la CER unica attiva
            cer_config = CERConfiguration.objects.filter(is_active=True).first()

            # Verifica compatibilità cabina primaria
            compatible = False
            if cer_config and pod_result.cabina_primaria:
                # Confronta il codice della cabina primaria del POD con quella della CER
                compatible = pod_result.cabina_primaria == cer_config.primary_substation

            return JsonResponse(
                {
                    "status": "success",
                    "pod_info": {
                        "pod": pod_result.pod,
                        "cabina_primaria": pod_result.cabina_primaria,
                        "fornitore": pod_result.fornitore,
                        "regioni": pod_result.regioni,
                        "province": pod_result.province,
                        "comuni": pod_result.comuni,
                    },
                    "cer_info": {
                        "id": cer_config.id if cer_config else None,
                        "name": cer_config.name if cer_config else "CER Unica",
                        "description": (
                            cer_config.description
                            if cer_config
                            else "Comunità Energetica Rinnovabile"
                        ),
                        "primary_substation": (
                            cer_config.primary_substation if cer_config else None
                        ),
                    },
                    "compatible": compatible,
                }
            )

    except ValueError as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
    except RuntimeError as e:
        # Errore specifico del POD resolver (POD non trovato, servizio non
        # disponibile, etc.)
        error_msg = str(e)
        if "Area Convenzionale non trovata" in error_msg:
            # API GSE non disponibile - permettere di procedere con POD valido
            logger.warning(
                f"API GSE non disponibile per POD {pod_code}, ma codice valido - "
                f"procedendo con dati limitati"
            )

            # Trova CER disponibili (senza filtri geografici)
            available_cer = CERConfiguration.objects.filter(is_active=True).values(
                "id", "name", "description"
            )

            return JsonResponse(
                {
                    "status": "success",
                    "pod_info": {
                        "pod": pod_code,
                        "cabina_primaria": "Non disponibile (API GSE non disponibile)",
                        "fornitore": "Non disponibile (API GSE non disponibile)",
                        "regioni": [],
                        "province": [],
                        "comuni": [],
                    },
                    "available_cer": list(available_cer),
                    "can_create_new": True,
                    "suggested_cer_name": "CER Nuova",
                    "warning": "Il servizio GSE per la risoluzione POD non è "
                    "attualmente disponibile. Il codice POD è valido e puoi "
                    "procedere con la configurazione.",
                }
            )
        else:
            logger.warning(f"Errore POD resolver per {pod_code}: {e}")
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Servizio di risoluzione POD temporaneamente non "
                    "disponibile. Riprova più tardi.",
                    "error_type": "service_unavailable",
                },
                status=503,
            )
    except Exception as e:
        logger.error(f"Errore imprevisto nella risoluzione POD {pod_code}: {e}")
        return JsonResponse(
            {
                "status": "error",
                "message": "Errore interno del server. Contatta il supporto se il "
                "problema persiste.",
                "error_type": "internal_error",
            },
            status=500,
        )


@login_required
def onboarding_status(request):
    """API per ottenere lo stato dell'onboarding"""
    user = request.user

    try:
        member_profile = user.member_profile
        onboarding_data = getattr(member_profile, "onboarding_data", {})

        return JsonResponse(
            {
                "status": "success",
                "onboarding_status": user.onboarding_status,
                "completed_steps": len(onboarding_data),
                "total_steps": 5,
                "progress_percentage": (len(onboarding_data) / 5) * 100,
            }
        )
    except MemberProfile.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Profilo membro non trovato"}, status=404
        )


@login_required
def profile_completion(request):
    """View per il completamento del profilo anagrafico"""
    user = request.user

    # Verifica che l'utente sia nel giusto stato
    if user.onboarding_status != CustomUser.OnboardingStatus.REGISTRATO:
        messages.warning(request, _("Il tuo profilo è già stato completato."))
        return redirect("core:dashboard")

    # Ottieni o crea il profilo membro
    try:
        member_profile = user.member_profile
    except MemberProfile.DoesNotExist:
        member_profile = MemberProfile.objects.create(user=user)

    if request.method == "POST":
        # Gestisci cambio tipo di soggetto
        if (
            "legal_type" in request.POST and len(request.POST) == 2
        ):  # Solo legal_type + CSRF
            legal_type = request.POST.get("legal_type")
            if legal_type and user.legal_type != legal_type:
                # Aggiorna senza validazione per evitare errori su campi non ancora
                # compilati
                CustomUser.objects.filter(pk=user.pk).update(legal_type=legal_type)
                user.refresh_from_db()
                messages.info(
                    request,
                    _("Tipo di soggetto aggiornato. Compila i campi appropriati."),
                )

        form = ProfileCompletionForm(request.POST, instance=member_profile, user=user)

        if form.is_valid():
            # Salva il profilo membro
            form.save()

            # Aggiorna il tipo di soggetto dell'utente se modificato
            legal_type = form.cleaned_data.get("legal_type")
            if legal_type and user.legal_type != legal_type:
                # Aggiorna senza validazione per evitare errori su campi non ancora
                # compilati
                CustomUser.objects.filter(pk=user.pk).update(legal_type=legal_type)
                user.refresh_from_db()

            # Aggiorna lo stato di onboarding
            CustomUser.objects.filter(pk=user.pk).update(
                onboarding_status=CustomUser.OnboardingStatus.ANAGRAFICA_COMPLETA
            )
            user.refresh_from_db()

            messages.success(
                request,
                _(
                    "Profilo anagrafico completato con successo! Ora puoi "
                    "procedere con la configurazione della CER."
                ),
            )

            return redirect("core:dashboard")
        else:
            messages.error(
                request, _("Ci sono errori nel form. Controlla i campi evidenziati.")
            )
    else:
        form = ProfileCompletionForm(instance=member_profile, user=user)

    context = {
        "form": form,
        "user": user,
        "member_profile": member_profile,
    }

    return render(request, "cer/profile_completion.html", context)
