read -p "Enter tag message: " desc
read -p "Enter release version: " VERSION
git tag -a "v$VERSION"  -m "$desc"
git commit -m "$desc"
git push origin "v$VERSION"
