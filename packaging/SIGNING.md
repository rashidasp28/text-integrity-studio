# Platform signing plan

The v0.8.0 release candidate is checksummed but unsigned.

## Windows

Obtain an organisation-controlled Authenticode certificate, protect the key in
a restricted signing service, sign after packaging and verify with `signtool`.

## macOS

Use an Apple Developer ID Application identity, hardened runtime, notarisation
and stapling. Verify with `codesign` and `spctl`.

## Linux

Publish SHA-256 checksums and decide whether the chosen package channel also
requires a detached GPG or Sigstore signature.

After credentials and verification steps are configured, add an intentionally
reviewed `packaging/SIGNING-READY` gate file. Never commit private keys,
certificate passwords or signing tokens.
