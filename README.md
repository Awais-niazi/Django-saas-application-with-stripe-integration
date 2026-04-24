# Django SaaS Demo

A Django SaaS-style demo app with authentication, profiles, protected pages, subscription models, and early Stripe integration.

The project is set up to be a strong learning repo first:
- simple Django app structure
- deployable on Render
- local SQLite for development
- Postgres via `DATABASE_URL` in hosted environments

## Features

- Django 5 app structure split into focused apps
- `django-allauth` for account flows
- profile listing and profile detail pages
- permission-oriented subscription models
- basic page visit tracking
- WhiteNoise static file serving
- Render blueprint config in [render.yaml](render.yaml)

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the environment template and adjust values as needed:

```bash
cp .env.example .env
```

4. Run migrations:

```bash
python src/manage.py migrate
```

5. Start the dev server:

```bash
python src/manage.py runserver
```

## Environment Variables

The main variables are documented in [.env.example](.env.example).

Important ones:
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `STRIPE_SECRET_KEY`

## Deploy on Render

This repo includes a Render Blueprint in [render.yaml](render.yaml).

Render docs I aligned this setup with:
- Django on Render: https://render.com/docs/deploy-django
- Blueprint spec: https://render.com/docs/blueprint-spec
- Deploy to Render button: https://render.com/docs/deploy-to-render

### Recommended path

1. Push this repo to GitHub.
2. In Render, open `Blueprints`.
3. Create a new Blueprint instance from the repo.
4. Review the generated web service and database.
5. Set any optional secrets such as `STRIPE_SECRET_KEY`.
6. Deploy.

### Current Render notes

- The web service is configured for the `free` plan in `render.yaml`.
- The database is also configured as `free` by default for easy one-click setup.
- As of April 18, 2026, Render’s docs say free Postgres databases expire after 30 days. If you want a longer-lived public demo, change the database plan in `render.yaml` from `free` to `basic-256mb` before deploying.
- The Blueprint sets `autoDeploy: false` so that people using the Deploy button do not accidentally redeploy their instance whenever this public repo changes. If you use this as your own main Render app, you can turn auto-deploy back on in the Render dashboard.

### Deploy Button

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Awais-niazi/Django-saas-application-with-stripe-integration)

## Project Notes

- Stripe is optional at startup. If `STRIPE_SECRET_KEY` is not set, the app will still boot.
- This repo is meant as a learning/demo project, not a hardened production SaaS.
- Some billing flows are still incomplete and should be treated as educational scaffolding.
