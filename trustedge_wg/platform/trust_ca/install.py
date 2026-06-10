from __future__ import annotations

import logging
import subprocess
import sys

log = logging.getLogger("trustedge-wg")


def install_policy_ca_if_requested(opts, api_client) -> None:
    """Download and optionally install block-page CA when --install-policy-ca is set."""
    if not getattr(opts, "install_policy_ca", False):
        return
    if not opts.api_url.strip():
        log.warning("--install-policy-ca requires --api-url")
        return
    if api_client is None:
        log.warning("--install-policy-ca skipped: no API client")
        return

    try:
        ca_pem = api_client.fetch_block_page_ca()
    except Exception as e:
        log.warning("could not download policy CA: %s", e)
        return

    if sys.platform == "darwin":
        from trustedge_wg.platform.trust_ca.darwin import install_trusted_root_ca

        try:
            install_trusted_root_ca(ca_pem)
        except subprocess.CalledProcessError as e:
            log.warning("failed to install policy CA (sudo?): %s", e)
        except Exception as e:
            log.warning("failed to install policy CA: %s", e)
        return

    log.warning("--install-policy-ca is only automated on macOS; install CA manually on this OS")
