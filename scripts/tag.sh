read -p "Enter tag message: " desc
export BRANCH=$(git branch | sed -n -e 's/^\* \(.*\)/\1/p')
git tag -a "v$BRANCH"  -m "$desc"
git commit -m "$desc"
git push origin "v$BRANCH"
