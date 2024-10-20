All contributions and ideas are welcome.

### 1. Clone the repo

With ssh (recommended):
```bash
git clone git@github.com:LearnWithHomer/sql_dependency_graph.git
```

### 2. Create your branch

Depending on what you are hoping to do with your branch, you may prefix it.

``` bash
#### Navigate to main branch
git checkout main

#### Ensure you have the latest changes
git status
git fetch origin -p
git rebase origin/main main

#### Create new additions
git checkout -b feature/{issue-description} 

#### Create a quick fix
git checkout -b hotfix/{issue-description}
```

### 3. Working on your feature branch

Run a `git diff` If there are any unknown changes since the last versioning, you can note this. 

You should be based off of branch `main`. Commit your code like normal, and if there has been a day or more between your last commit, you may need to rebase your changes on top of the latest commits (head) of `main`. 

Fetch the latest changes from all branches (and prune any deleted branches):
```bash
git fetch origin -p
```

Next ensure your local `main` has all of the changes that the remote `main` has.
```bash
git rebase origin/main main
```

Ensure your feature branch has all of the changes in `main` in it.
```bash
git rebase main feature/my-feature-branch-name-here
```

When you rebase `main` into your feature branch, you will need to force-push it to the repo. PLEASE BE EXTRA CAREFUL with this - only use force push on a feature branch that only you have worked on, otherwise you may overwrite other peoples commits, as it will directly modify the repo's git history. 
```bash
git push origin feature/my-feature-branch-name-here --force
```

### 4. Creating a PR

You'll need to make a PR. Write tests for python and fill out the PR checklist.

Please open a pull request via the github UI and request to merge into `main`. Once there has been a successful review of your PR, and the automated tests pass, then feel free to merge at your leisure.

Preface PRs with "[WIP]" if you are still working on them and "[READY]" if you're good to go.
