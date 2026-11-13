# PREDICT/90 auto run

Every morning (05:30 Nigeria time) GitHub runs the predictor by itself and puts the results page on your own
private link. No PC, no Colab: open the link on your phone and type your password once.

## Set it up once (about 5 minutes)

1. Make a free account on github.com.
2. On this page press **Use this template** > **Create a new repository**. Give it any name, keep it **Public**
   (free GitHub Pages needs it). Your page is locked with your password, so nobody else can read it.
3. In your new repository: **Settings** > **Secrets and variables** > **Actions** > **New repository secret**, twice:
   - Name `API_FOOTBALL_KEY`, value: your API-Football key (the same one as in your .env file)
   - Name `PAGE_PASSWORD`, value: a password you choose (at least 6 characters)
4. **Settings** > **Pages** > Source: **GitHub Actions**.
5. **Actions** tab > **Daily predictions** > **Run workflow** > **Run workflow**. The first run takes about
   20-30 minutes (it downloads 20 years of results and trains the models). After that about 5 minutes a day.
6. Your link: `https://YOUR-USERNAME.github.io/YOUR-REPOSITORY-NAME/` - save it on your phone's home screen.

## Good to know

- Need fresh predictions now? Actions > Daily predictions > Run workflow.
- The page has a Download bar: the Excel file of the day and your bet tracker.
- It uses the same API-Football key as your PC and Colab: about 10-40 of the 100 free requests a day.
- The code updates by itself (same code as the Colab link), so fixes arrive with no work on your side.
- Your own settings: add a file `settings.json` to this repository (same format as in the PC version).
- If a run fails, GitHub sends you an email. The page then still shows the last good run.
