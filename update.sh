python setup.py clean
read -p "Enter commit message: " desc
git commit -m "$desc"
export BRANCH=$(git branch | sed -n -e 's/^\* \(.*\)/\1/p')
cmd="sed 's/VERSION/$BRANCH/g'"
cat entangle/__version_tmpl__.py | eval $cmd >entangle/__version__.py
git add entangle/__version__.py
git commit -m "Updated version"
git push origin $BRANCH
