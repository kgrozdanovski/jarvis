# Contributing

The following is a guide towards contributing to the Jarvis project.
This document describes the typical workflow, the coding standards, branching strategy
and the commit message conventions.

## Coding Standards

The Coding Standard enforced in this project follows [PEP-8](https://peps.python.org/pep-0008/).

## Commit Messages

The commit messages should follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
specification. This enables us to automate the versioning and changelog generation process. If the commit
message does not follow the specification, the CI/CD pipeline will fail the build.

## Pull Request Process

1. Before creating a pull request, make sure that your branch is up-to-date with the `master` branch.
   This can be done by switching to the `master` branch and pulling the latest changes from the remote
   repository. Then switch back to your branch and rebase your branch onto the `master` branch.
2. Ensure that any and all existing tests pass successfully, including Code Quality and Unit tests.
3. Make sure that the code is properly documented and that the documentation is up-to-date.
4. You may merge the pull request in once you have a code review from at least one other developer,
   or if you do not have permission to do that, you may request the second reviewer to merge it for you.

## Versioning

The versioning scheme we use is [SemVer](http://semver.org/) and the format is as follows:
`<major>.<minor>.<patch>`.
The version is automatically bumped by the CI/CD pipeline when a new tag is pushed to the repository.
