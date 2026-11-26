# Upload this project to GitHub

## Option A — Git command line (recommended)

1. Create or sign in to your account at <https://github.com>.
2. Select **New repository**. Name it `telecom-customer-churn-analysis`.
3. Set the repository to **Public** if you want to show it in a portfolio, or **Private** if this is only for coursework. Do not initialise it with an extra README, license, or `.gitignore` because this project already contains those files.
4. Open PowerShell in the `telco-churn-project` folder (the folder containing `README.md`).
5. Run these commands, replacing `YOUR_USERNAME` with your GitHub username:

```powershell
git init
git add .
git status
git commit -m "Add telecom customer churn analysis project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/telecom-customer-churn-analysis.git
git push -u origin main
```

6. Refresh the repository page. Confirm that `README.md`, `notebooks/`, `src/`, `tests/`, and `requirements.txt` are visible.

If Git asks you to identify yourself, configure the name and email attached to your GitHub account:

```powershell
git config --global user.name "Your Name"
git config --global user.email "YOUR_GITHUB_EMAIL"
```

If GitHub asks for a password over HTTPS, use the authentication flow presented by Git Credential Manager or a personal access token; your normal GitHub account password is not accepted for Git operations.

## Option B — GitHub Desktop

1. Install GitHub Desktop from <https://desktop.github.com/> and sign in.
2. Choose **File → Add Local Repository** and select this project folder.
3. If prompted that the folder is not a Git repository, choose **Create a Repository** and use the project folder as the local path.
4. Enter a summary such as `Add telecom customer churn analysis project`, then choose **Commit to main**.
5. Select **Publish repository**, choose the visibility, and publish.

## Before sharing or submitting

- Add your name, course, and submission date to the README if required.
- Run the setup and analysis commands in the README on your computer. This downloads the real source CSV, executes the analysis, and generates reports locally.
- Run the unit tests: `py -m unittest discover -s tests -v`.
- Check the notebook by opening it and selecting **Run All** after the dataset has downloaded.
- Keep `data/raw/Telco-Customer-Churn.csv` out of Git unless your course specifically requires the data file. It is ignored by `.gitignore`; the downloader obtains and verifies the IBM source CSV on a fresh machine.
- Never commit `.venv/`, passwords, API tokens, or other private credentials.

## Common Git fixes

**`git` is not recognised:** Install Git for Windows from <https://git-scm.com/download/win>, reopen PowerShell, and retry.

**`remote origin already exists`:** Run `git remote set-url origin https://github.com/YOUR_USERNAME/telecom-customer-churn-analysis.git` and retry the push.

**Push rejected because the remote contains a README:** If you created the GitHub repository with an initial README, license, or `.gitignore`, the remote has a commit that your local repository does not. The simplest clean fix for a new project is to create a fresh empty GitHub repository, or merge the remote history deliberately rather than force-pushing blindly.
