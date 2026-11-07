"""Weekly job: extend the Instagram long-lived token (valid 60 days) and store it back in GitHub Secrets.

Needs GH_PAT (fine-grained token with 'Secrets: read and write' on this repo) to save a changed token.
"""
import os, subprocess, sys
from . import instagram


def main():
    res = instagram.refresh_token()
    if not res:
        print("Token not refreshed (too new, or invalid). Nothing to do."); return
    token, expires = res
    print(f"Token refreshed, valid for {int(expires or 0)//86400} more days.")
    if token and token != os.environ["IG_ACCESS_TOKEN"]:
        if not os.environ.get("GH_PAT"):
            print("Instagram returned a NEW token but GH_PAT is not set, so it can't be saved. Add GH_PAT."); sys.exit(1)
        subprocess.run(["gh", "secret", "set", "IG_ACCESS_TOKEN", "--body", token, "--repo", os.environ["GITHUB_REPOSITORY"]],
                       check=True, env={**os.environ, "GH_TOKEN": os.environ["GH_PAT"]})
        print("Saved the new token to the IG_ACCESS_TOKEN secret.")


if __name__ == "__main__":
    main()
