# Here be dragons

This project is in its very early stages. Tame your expectations and excercise caution.

## What is this?

Quorra is an OIDC compatible IDP (identity provider).

While other providers either use a password, WebAuthn, OTPs or a combination of the three, Quorra uses asymetric encryption. The private key is stored on a device running one of Quorra's keychain apps.

It doesn't aim to be a replacement for other identity providers, instead Quorra is meant to be used *alongside* other more full-featured IDPs like [Authentik](https://goauthentik.io/), [Zitadel](https://zitadel.com/), [Keycloak](https://keycloak.org/), [Dex](https://dexidp.io/), etc.

As such, Quorra only implements a fairly minimal set of OIDC features and doesn't provide any access controls. It wasn't created to plug directly into your applications, it is to be used as an external identity provider for your existing IDP.

For simple use-cases without the need for fine-grained access policies it can be used by your applications directly.

## Can I see?

Registration:

https://github.com/user-attachments/assets/687c9122-084a-487e-b4b1-2e65ddf03042

Login:

https://github.com/user-attachments/assets/eee12b01-fc50-440f-a4ba-23cb955ddd28

## Who is it for?

Quorra is for everyone, but the main target audience are home users and self-hosters.

## What about the mobile app?

As a starting point we provide two first-party apps for two platforms:

* [Voucher](https://github.com/k8ieone/voucher) is a client for Linux written in Python and GTK4/Libadwaita
* [Flare](https://github.com/Quorra-Auth/flare) is a client for Android written in Flutter

Other applications compatible with [LNURL-auth (LUD-04)](https://github.com/lnurl/luds/blob/luds/04.md) should work with Quorra out of the box, just without Quorra-specific features.

Tested applications that can be used to hold your private keys:

- [Phoenix](https://github.com/ACINQ/phoenix)
- [BlueWallet](https://github.com/bluewallet/bluewallet)
- [Zeus](https://github.com/ZeusLN/zeus)
- [Blixt Wallet](https://blixtwallet.github.io/)
- [Misty Breez](https://github.com/breez/misty-breez)

We hope developers will pick up development of their own authenticator apps for Quorra. The API is documented using OpenAPI and we try to keep it simple.
## How does it work?

Everything in Quorra is based either on short-term random secrets or asymetric encryption. No magic involved.

## Is this safe?

This project is not ready for production use yet and it is too early to start chasing down potential security issues. Anything can change at any point. DO NOT USE IN PRODUCTION unless you're okay with getting pwned.

## How do I deploy this?

TODO

If you're ready to start playing with Quorra... TBD
