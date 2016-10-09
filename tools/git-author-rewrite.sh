#!/bin/sh -x
#
# only slightly modified from https://help.github.com/articles/changing-author-info/

for repo in coursera-ml asp-class PictureLab Magpie FracCalc Scripts TestExcel Elevens
do
    git clone --bare https://wcyuan:password@github.com/wcyuan/${repo}.git
    cd ${repo}.git
    git filter-branch --env-filter '
OLD_EMAIL="oldname@domain.com"
CORRECT_NAME="Correct Name"
CORRECT_EMAIL="newname@domain.com"
if [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_COMMITTER_NAME="$CORRECT_NAME"
    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
fi
if [ "$GIT_AUTHOR_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_AUTHOR_NAME="$CORRECT_NAME"
    export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
fi
' --tag-name-filter cat -- --branches --tags
    git push --force --tags origin 'refs/heads/*'
    cd ..
    rm -rf ${repo}.git
done
