read -p "Enter tag message: " desc
read -p "Enter release version (e.g. 0.1.9): " VERSION
git tag -a "v$VERSION"  -m "$desc"
git commit -m "$desc"
git push origin "v$VERSION"
