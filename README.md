# jackrsteiner.github.io

Root GitHub Pages site for `https://jackrsteiner.github.io`.

This repo generates a simple index of public project Pages sites such as:

```text
https://jackrsteiner.github.io/example-repo/
```

The generated root page is deployed to:

```text
https://jackrsteiner.github.io
```

## How it works

The GitHub Action in `.github/workflows/build-index.yml` runs `scripts/build_index.py`.

The script:

1. lists public repositories for `jackrsteiner`;
2. checks which repositories have GitHub Pages enabled;
3. keeps normal project Pages URLs under `https://jackrsteiner.github.io/<repo>/`;
4. generates `public/index.html`;
5. deploys the generated page using GitHub Pages Actions.

## Setup

1. Create a GitHub repository named exactly:

   ```text
   jackrsteiner.github.io
   ```

2. Upload these files to the repo.

3. In the repo, go to **Settings → Pages**.

4. Under **Build and deployment**, choose **GitHub Actions**.

5. Go to the **Actions** tab and run **Build Pages Index** manually once.

After that, the workflow also runs automatically:

- when relevant files are pushed to `main`;
- once per day on the schedule.

## Edit your profile text

Change `profile.json`:

```json
{
  "name": "Jack Steiner",
  "headline": "Projects, experiments, and notes",
  "bio": "A small automatically generated index of public GitHub Pages projects.",
  "links": [
    {
      "label": "GitHub",
      "url": "https://github.com/jackrsteiner"
    }
  ]
}
```

## Optional behavior

The script supports these environment variables:

| Variable | Default | Purpose |
|---|---:|---|
| `OWNER` | `jackrsteiner` | GitHub username or organization name to scan. |
| `INCLUDE_FORKS` | false | Include forked repositories. |
| `INCLUDE_ARCHIVED` | false | Include archived repositories. |
| `INCLUDE_CUSTOM_DOMAINS` | false | Include Pages sites that use custom domains instead of `jackrsteiner.github.io/<repo>/`. |

For example, in the workflow:

```yaml
env:
  OWNER: jackrsteiner
  INCLUDE_FORKS: "true"
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Local test

From the repo root:

```bash
OWNER=jackrsteiner python scripts/build_index.py
```

Then open:

```text
public/index.html
```
