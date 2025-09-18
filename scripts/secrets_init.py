import os
import base64
import secrets


def write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
    secrets_dir = "/secrets"
    os.makedirs(secrets_dir, exist_ok=True)

    # Redis password
    rp = os.path.join(secrets_dir, "redis_password")
    if not os.path.exists(rp):
        pw = base64.urlsafe_b64encode(secrets.token_bytes(24)).decode().rstrip("=")
        write_file(rp, pw)

    # Application env (SECRET_KEY, FIELD_ENCRYPTION_KEY)
    ae = os.path.join(secrets_dir, "app.env")
    if not os.path.exists(ae):
        sk = base64.urlsafe_b64encode(secrets.token_bytes(50)).decode().rstrip("=")
        fk = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
        write_file(ae, f"SECRET_KEY={sk}\nFIELD_ENCRYPTION_KEY={fk}\n")

    print("secrets ready")


if __name__ == "__main__":
    main()


