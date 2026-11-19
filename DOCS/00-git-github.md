GIT AND GITHUB - FROM A NEW REPO TO THE FIRST PUSH

GOAL

Create a repo on GitHub, connect a project folder on your Mac to it, and push. The steps below are in the order that avoids every error listed at the end. After the first push, you only need the everyday loop.


THE BIG PICTURE

There are two copies of the repo:

- Local: the folder on your Mac. git add and git commit only change this copy.
- Remote: the repo on GitHub, called "origin". Only git push sends commits there, and only git pull brings them back.

```
your files  --git add-->  staged  --git commit-->  local repo  --git push-->  GitHub
                                                   local repo  <--git pull--  GitHub
```

A commit that has not been pushed exists only on your Mac. If the GitHub page looks empty, the commits have not been pushed yet.


ONE-TIME CHECK: SSH KEY (once per Mac)

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
mkdir -p ~/Documents/pw-learn/DOCS ~/Documents/pw-learn/FILES
cd ~/Documents/pw-learn
pwd
git init -b main
```

- pwd confirms you are in the right folder. Check it before every git init.
- git init -b main creates the local repo with the branch name "main".


STEP 3 - CREATE .GITIGNORE BEFORE ANYTHING ELSE

In VS Code, create a file called .gitignore in the repo root and paste:

```
# Python
.venv/
__pycache__/
*.pyc
.pytest_cache/

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


STEP 4 - ADD YOUR PROJECT FILES

Create the venv, install the packages, and add the files (README.md, pytest.ini, requirements.txt, DOCS/, FILES/). See DOCS/01-setup.md.

When a doc gives a file's contents, paste only the contents into the file in VS Code. Lines like cat > file << 'EOF' and EOF are terminal commands, never part of the file.


STEP 5 - THE FIRST COMMIT

```
git status
git add .gitignore README.md pytest.ini requirements.txt DOCS FILES
git status
git commit -m "Module 01: setup"
git log --oneline
```

- The first git status shows what is new. .venv/ must NOT be listed.
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

It should say "Your branch is up to date with 'origin/main'". Refresh the repo page on GitHub: your files are there, and .venv is not.


EVERYDAY LOOP (after the first push)

```
cd ~/Documents/pw-learn
source .venv/bin/activate
git pull
```

Work on your files, then:

```
git status
git add <files>
git commit -m "Module NN: topic"
git push
```

- Start every session with git pull, especially if anything was changed on the GitHub website.
- Make changes in one place: either your Mac or the website, not both at the same time.
- If you pushed but GitHub looks unchanged, check git status: "Your branch is ahead of 'origin/main'" means there are commits that were not pushed.


ON ANOTHER MAC (THE REPO ALREADY HAS FILES)

```
cd ~/Documents
git clone git@github.com:<your-username>/pw-learn.git
cd pw-learn
```

clone downloads the repo and sets up origin and the link to main automatically. No git init, remote add or -u needed. Then create the venv and install from requirements.txt.


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

Untracked files: FILES/
  Those files were never added. Run git add FILES, then commit.


WHY IT MATTERS / TRAPS (READ THIS PART!)

Trap 1 - Commit is not push.
git commit only saves on your Mac. GitHub only changes after git push.

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

Trap 8 - Editing on GitHub and on your Mac at the same time.
This gives divergent branches. Pull first, and keep changes in one place.

Trap 9 - Your email in public commits.
Every commit stores the author's email. Not a concern for a private repo. Before making a repo public, set GitHub's private no-reply address (Settings -> Emails) - ideally before the first commit.


MENTAL MODEL

- Once per Mac: SSH key.
- Once per repo: empty GitHub repo -> git init -b main -> .gitignore -> first commit -> git remote add origin -> git push -u origin main.
- Every session: git pull -> work -> git add -> git commit -> git push.


QUIZ (answers below - try before peeking)

1. You committed three times, but the GitHub page is still empty. Why?

2. git push says "src refspec main does not match any". What is the most likely cause?

3. Why does the first push need -u, and the later ones do not?

4. git status shows "Untracked files: FILES/". Is FILES/ in your last commit?

5. You created the GitHub repo with "Add a README" ticked, and the first push is rejected. What do you do?

6. You ran git add .gitignore yesterday but never committed. Today you commit only README.md. What does that commit contain?


ANSWERS

1. The commits are only on your Mac. Nothing reaches GitHub until git push.

2. There are no commits yet, so the branch does not exist. Make the first commit, then push.

3. -u links your local main to main on GitHub. Once the link exists, Git remembers it.

4. No. Untracked means it was never added. Run git add FILES and commit it.

5. Run git pull origin main --allow-unrelated-histories, then git push. Or delete the GitHub repo and create it again, empty.

6. Both README.md and .gitignore, because .gitignore was already staged. Check git status before every commit