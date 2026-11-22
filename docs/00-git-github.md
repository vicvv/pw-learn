GIT AND GITHUB - FROM A NEW REPO TO THE FIRST PUSH


GOAL

Create a repo on GitHub, connect a project folder on your computer (Mac or Windows PC) to it, and push. The steps below are in the order that avoids every error listed at the end. After the first push, you only need the everyday loop.

Commands are for macOS (zsh). Where Windows (PowerShell) differs, the Windows command is given too. Git commands themselves are the same on every system.


THE BIG PICTURE

There are two copies of the repo:

- Local: the folder on your computer. git add and git commit only change this copy.
- Remote: the repo on GitHub, called "origin". Only git push sends commits there, and only git pull brings them back.

```
your files  --git add-->  staged  --git commit-->  local repo  --git push-->  GitHub
                                                   local repo  <--git pull--  GitHub
```

A commit that has not been pushed exists only on your computer. If the GitHub page looks empty, the commits have not been pushed yet.


ONE-TIME CHECK: SSH KEY (once per computer)

```
ssh -T git@github.com
```

- "Hi <your-username>! You've successfully authenticated" means the key works. ("does not provide shell access" in the same message is normal.)
- "Permission denied (publickey)" means there is no key yet. Follow GitHub's guide: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

With SSH, no token is ever stored in the repo.


STEP 1 - CREATE AN EMPTY REPO ON GITHUB

1. Go to https://github.com/new
2. Repository name: pw-learn
3. Private or Public. Private is safer while you are working. It can be switched later under Settings.
4. Leave "Add a README", ".gitignore" and "license" UNTICKED. The repo must be empty.
5. Click Create repository.

GitHub then shows a "Quick setup" page with commands. Ignore them: they are for a different starting point, and the echo command would add a line to your README.


STEP 2 - CREATE THE PROJECT FOLDER AND LOCAL REPO

```
mkdir -p ~/Documents/pw-learn/docs ~/Documents/pw-learn/tests ~/Documents/pw-learn/src/pw_learn/pages
cd ~/Documents/pw-learn
pwd
git init -b main
```

- mkdir -p creates all these folders at once, including the parent folders.
- pwd confirms you are in the right folder. Check it before every git init.
- git init -b main creates the local repo with the branch name "main".
- On Windows, create the folders in File Explorer or VS Code, then run the git commands in PowerShell from inside the pw-learn folder.


STEP 3 - CREATE .GITIGNORE BEFORE ANYTHING ELSE

In VS Code, create a file called .gitignore in the repo root and paste:

```
# Python
.venv/
__pycache__/
*.pyc
.pytest_cache/

# Python packaging
*.egg-info/
build/
dist/

# Playwright output
test-results/
playwright-report/

# Secrets and saved login state
.env
auth/
*.storage.json

# Editors and OS
.vscode/
.idea/
.DS_Store
```

Creating it first means .venv and other junk can never be committed by accident.

*.egg-info/ matters in this project: pip install -e . (docs/01-setup.md, section 6) creates a src/pw_learn.egg-info/ folder, and it must never be committed.


STEP 4 - ADD YOUR PROJECT FILES

Create the venv, install the packages, and add the project files: README.md, pyproject.toml, pytest.ini, requirements.txt, docs/, src/ and tests/. See docs/01-setup.md.

When a doc gives a file's contents, paste only the contents into the file in VS Code. Lines like cat > file << 'EOF' and EOF are terminal commands that create a file from the shell. They are never part of the file itself.


STEP 5 - THE FIRST COMMIT

```
git status
git add .gitignore README.md pyproject.toml pytest.ini requirements.txt docs src tests
git status
git commit -m "Module 01: setup"
git log --oneline
```

- The first git status shows what is new. .venv/ and pw_learn.egg-info/ must NOT be listed. If they are, fix .gitignore first.
- The second git status shows what will be committed (green, under "Changes to be committed"). Check nothing is missing.
- git log --oneline should show your commit.

A branch only exists after its first commit. Pushing before this step gives "src refspec main does not match any".


STEP 6 - CONNECT THE LOCAL REPO TO GITHUB

```
git remote add origin git@github.com:<your-username>/pw-learn.git
git remote -v
```

- origin is the usual name for the GitHub copy.
- git remote -v should show the address twice (fetch and push).
- This is done once per repo.


STEP 7 - THE FIRST PUSH (WITH -u)

```
git push -u origin main
```

- -u links your local main branch to main on GitHub. This is needed once, on the first push.
- After this, plain git push and git pull work.


STEP 8 - CHECK

```
git status
```

It should say "Your branch is up to date with 'origin/main'". Refresh the repo page on GitHub: your files are there, and .venv and pw_learn.egg-info are not.


EVERYDAY LOOP (after the first push)

```
cd ~/Documents/pw-learn
source .venv/bin/activate
git pull
```

On Windows, activate with .venv\Scripts\Activate.ps1 instead.

Work on your files, then:

```
git status
git add <files>
git commit -m "Module NN: topic"
git push
```

- Start every session with git pull, especially if anything was changed on the GitHub website.
- Make changes in one place: either your computer or the website, not both at the same time.
- If you pushed but GitHub looks unchanged, check git status: "Your branch is ahead of 'origin/main'" means there are commits that were not pushed.


ON ANOTHER COMPUTER (THE REPO ALREADY HAS FILES)

```
cd ~/Documents
git clone git@github.com:<your-username>/pw-learn.git
cd pw-learn
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
pytest -v
```

- clone downloads the repo and sets up origin and the link to main automatically. No git init, remote add or -u needed.
- The venv is not in the repo (it is in .gitignore), so every computer creates its own.
- pip install -r requirements.txt installs the pinned packages and, because of the -e . line, the pw_learn package too.
- Browsers are not in the repo either, so playwright install chromium is needed on every computer.
- On Windows: python -m venv .venv, then .venv\Scripts\Activate.ps1. The other commands are the same.


ERRORS AND WHAT THEY MEAN

error: src refspec main does not match any
  There are no commits yet, or the branch is called master. Make the first commit (Step 5). If git branch shows master: git branch -M main

There is no tracking information for the current branch
  git pull was run before the first push. Skip the pull and do the first push with -u (Step 7).

fatal: The current branch main has no upstream branch
  The first push was a plain git push. Run git push -u origin main.

error: remote origin already exists
  The remote was already added. To change it: git remote set-url origin git@github.com:<your-username>/pw-learn.git

Permission denied (publickey)
  The SSH key is missing or not added to GitHub. See ONE-TIME CHECK.

! [rejected] main -> main (fetch first)
  GitHub has commits you do not have (for example, a README created on the website). Run git pull --rebase, then git push.

You have divergent branches and need to specify how to reconcile them
  Both sides have new commits. Run git pull --rebase. To make it the default for this repo: git config pull.rebase true

error: cannot pull with rebase: You have unstaged changes
  Commit (or undo) your local changes first, then pull.

Untracked files: tests/
  Those files were never added. Run git add tests, then commit.

Untracked files: src/pw_learn.egg-info/
  .gitignore is missing the packaging lines. Add *.egg-info/ to .gitignore (Step 3). Do not commit the folder.


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Commit is not push.
git commit only saves on your computer. GitHub only changes after git push.

Trap 2 - Pushing before the first commit.
There is no branch to push yet. Commit first.

Trap 3 - Pulling before the first push.
There is nothing on GitHub to pull from. git pull only belongs in the routine after the first push.

Trap 4 - Forgetting -u on the first push.
Without it, Git does not know where main should go.

Trap 5 - Creating the GitHub repo with a README.
The two histories no longer match and the first push is rejected. Create it empty.

Trap 6 - Staged files that never get committed.
git add without git commit leaves files waiting. The next commit, for any other file, includes them too. Run git status before every commit.

Trap 7 - Pasting commands into files.
Only file contents go into a file. A cat or EOF line inside a .py file breaks it.

Trap 8 - Editing on GitHub and on your computer at the same time.
This gives divergent branches. Pull first, and keep changes in one place.

Trap 9 - Your email in public commits.
Every commit stores the author's email. Not a concern for a private repo. Before making a repo public, set GitHub's private no-reply address (Settings -> Emails) - ideally before the first commit.

Trap 10 - Committing build leftovers.
pip install -e . creates src/pw_learn.egg-info/. Without *.egg-info/ in .gitignore, git add src would commit it.


MENTAL MODEL

- Once per computer: SSH key.
- Once per repo: empty GitHub repo -> git init -b main -> .gitignore -> first commit -> git remote add origin -> git push -u origin main.
- Every session: git pull -> work -> git add -> git commit -> git push.
- A new computer: git clone -> venv -> pip install -r requirements.txt -> playwright install chromium.


QUIZ (answers below - try before peeking)

1. You committed three times, but the GitHub page is still empty. Why?

2. git push says "src refspec main does not match any". What is the most likely cause?

3. Why does the first push need -u, and the later ones do not?

4. git status shows "Untracked files: tests/". Is tests/ in your last commit?

5. You created the GitHub repo with "Add a README" ticked, and the first push is rejected. What do you do?

6. You ran git add .gitignore yesterday but never committed. Today you run git add README.md and commit. What does that commit contain?

7. git status lists "Untracked files: src/pw_learn.egg-info/". Should you commit it? What do you do?


ANSWERS


1. The commits exist only on your computer. Nothing reaches GitHub until you run git push (the first time: git push -u origin main).

Why: git commit saves a snapshot in your local repo. GitHub is a separate copy, and only git push sends commits to it. git log --oneline shows your local commits. git status says "Your branch is ahead of 'origin/main'" once the link exists and there are commits waiting to be pushed.

Common mistakes:
- Thinking a successful commit means the work is on GitHub. A commit message such as "[main 5c41b67] ..." only confirms the local save.
- Running plain git push on a brand-new repo. The first push needs -u origin main (answer 3).

See: THE BIG PICTURE, and Trap 1.


2. There are no commits yet, so the branch does not exist. Make the first commit, then push.

Why: a branch is a name pointing at a commit. Straight after git init, main has no commit to point at, so there is nothing to push. Less often, the branch is called master (repos created with plain git init on older Git). git branch shows the name, and git branch -M main renames it.

Common mistakes:
- Adding the remote and pushing straight after git init, before any git commit.

See: STEP 5, and Trap 2.


3. -u links your local main branch to main on GitHub. Git saves that link, so later pushes and pulls already know where to go.

Why: with the link saved, git push means "push main to origin's main" and git pull means "pull from origin's main". Without it, Git does not know the destination and stops with "The current branch main has no upstream branch". The link is set once, on the first push.

Common mistakes:
- Running git pull before the first push. There is no link yet and nothing on GitHub to pull, so it fails with "There is no tracking information for the current branch". Skip the pull and push with -u.

See: STEP 7, Trap 3 and Trap 4.


4. No. Untracked means Git has never been told about the folder, so it is in no commit at all. Run git add tests, then git commit.

Why: git commit only includes files that were staged with git add. A folder created after your last git add is invisible to every commit until you add it.

Common mistakes:
- Assuming everything in the project folder goes into a commit. Only what is staged goes in. Check git status before every commit: anything under "Untracked files" is not included.

See: STEP 5, and Trap 6.


5. Either combine the two histories with git pull origin main --allow-unrelated-histories and then git push, or delete the GitHub repo and create it again with nothing ticked, then push.

Why: ticking "Add a README" makes GitHub create a first commit that your local repo does not have. The two histories do not connect, so Git refuses to overwrite GitHub's commit. The problem is that commit, not the README file itself.
- Combining: if both sides have a README.md, Git stops with a conflict in that file. Choose a version, commit, then push.
- Starting over: simplest for a brand-new repo with nothing else on it.
- git push --force replaces GitHub's history with yours. Acceptable on a brand-new personal repo, never on a repo others use.

Common mistakes:
- Deleting the README on GitHub, then pulling. Deleting makes another commit on GitHub, and a plain pull refuses unrelated histories.

See: STEP 1, and Trap 5.


6. Both README.md and .gitignore. .gitignore was already staged from yesterday, and git commit includes everything that is staged, not only the file you added today.

Why: staging is a waiting area. Files stay there until a commit takes them. A commit does not ask which files you meant: it takes all of them.

Common mistakes:
- Expecting git add README.md to limit the commit to README.md. git add only adds to the waiting area, and other files already in it come along too. git status, under "Changes to be committed", shows exactly what the next commit will contain.

See: Trap 6.


7. No. It is generated by pip install -e . and belongs on your computer only. Add *.egg-info/ to .gitignore, and it disappears from git status.

Why: the folder holds information pip writes when it installs the package. It is recreated on every install, it differs between computers, and pip install -r requirements.txt rebuilds it on any new computer. Committing it would only add noise.

If it was already committed, stop tracking it without deleting it:

```
git rm -r --cached src/pw_learn.egg-info
git commit -m "Stop tracking egg-info"
```

Common mistakes:
- Deleting the folder. It is harmless and pip recreates it. The fix is .gitignore, so Git ignores it for good.
- Using git add -A or git add . before .gitignore is right. That commits whatever is lying around.

See: STEP 3, and Trap 10.