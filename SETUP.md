# One-time setup

This repository is ready to validate, translate, and publish ShiftMate Blogger content. The remaining setup is account credentials only.

## 1. OpenAI API key

Create a project-scoped API key in the OpenAI API platform and save the value immediately. The full secret key is only shown when it is created.

Add it to this repository:

`Settings -> Secrets and variables -> Actions -> New repository secret`

Name:

`OPENAI_API_KEY`

Do not commit or paste the key into source files, issues, or chat.

## 2. Google Blogger OAuth

In Google Cloud Console:

1. Enable **Blogger API v3**.
2. Configure Google Auth Platform if the project has not been configured yet.
3. Go to **Google Auth platform -> Clients**.
4. Create a client with **Application type: Desktop app**.
5. Copy the generated Client ID and Client Secret.

The automation requests only this Blogger scope:

`https://www.googleapis.com/auth/blogger`

On your own computer, clone this repository and run:

```bash
git clone https://github.com/nicelee777/Blogger.git
cd Blogger
python3 scripts/blogger_oauth_helper.py \
  --client-id 'YOUR_CLIENT_ID' \
  --client-secret 'YOUR_CLIENT_SECRET'
```

Approve the Google consent screen, then paste the full redirected localhost URL back into the terminal when prompted.

The helper prints these values:

- `BLOGGER_CLIENT_ID`
- `BLOGGER_CLIENT_SECRET`
- `BLOGGER_REFRESH_TOKEN`

Add all three to repository Actions secrets. Never commit them.

## 3. Repository Actions secrets

The final repository secret set must be:

- `OPENAI_API_KEY`
- `BLOGGER_CLIENT_ID`
- `BLOGGER_CLIENT_SECRET`
- `BLOGGER_REFRESH_TOKEN`

## 4. First Blogger connection test

Before any live publish:

1. Open **Actions -> Blogger - Publish -> Run workflow**.
2. Select `main`.
3. Set `dry_run` to `true`.
4. Run the workflow.

A successful dry run resolves the ShiftMate blog and all configured FAQ pages without modifying Blogger.

Expected FAQ paths:

- `/p/faq.html`
- `/p/faq-ko.html`
- `/p/faq-ja.html`
- `/p/faq-cn.html`
- `/p/faq-tw.html`
- `/p/faq-es.html`
- `/p/faq-vi.html`

## 5. First live publish

Only after the dry run output is correct:

1. Run **Blogger - Publish** again.
2. Set `dry_run` to `false`.
3. Confirm the seven FAQ pages on Blogger.

Normal operation after setup:

- edit Korean source on `develop`
- translation workflow generates/updates the other locales
- review changes
- merge reviewed content to `main`
- `main` publishes validated content to Blogger

See `blogger/README.md` for content structure and operating details.
