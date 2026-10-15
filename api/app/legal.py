"""The legal texts a user accepts, and their versions.

The acceptance wording and document versions are the old site's legal registry
(alphacouncil-static/legal/registry.json), unchanged; the documents themselves are
served by the web app from web/src/content/legal/. tests/test_accounts.py checks
that these versions match the documents the site shows.
"""

REGISTRATION = {
    "kind": "registration",
    "text_version": "1.0",
    "text": "I agree to the Terms of Service and acknowledge the Privacy Policy.",
    "documents": {"terms": "1.2", "privacy": "1.2"},
}
