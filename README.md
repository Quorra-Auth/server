# Here be dragons

This project is in its very early stages. Tame your expectations and excercise caution.

## What is this?

Quorra is an OIDC compatible IDP (identity provider).

It doesn't aim to be a replacement for other identity providers, instead Quorra is meant to be used *alongisde* other more full-featured IDPs like [Authentik](https://goauthentik.io/), [Zitadel](https://zitadel.com/), [Keyloak](https://keycloak.org/), [Dex](https://dexidp.io/), etc.

As such, Quorra only implements a fairly minimal set of OIDC features and doesn't provide any access controls. It wasn't created to plug directly into your applications, it is to be used as an external identity provider for your existing IDP.

For simple use-cases without the need for fine-grained access policies it can be used as a standalone IDP.

## Can I see?

TODO: Add a video

## Who is it for?

Quorra is for everyone, but the main target audience are home users and self-hosters.