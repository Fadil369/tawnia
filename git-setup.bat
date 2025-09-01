@echo off
echo Setting up GitHub repository...

git init
git add .
git commit -m "Initial commit: Tawnia Healthcare Analytics v2.0"

echo.
echo Create repository at: https://github.com/new
echo Repository name: tawnia-healthcare-analytics
echo.
echo Then run:
echo git remote add origin https://github.com/your-username/tawnia-healthcare-analytics.git
echo git branch -M main
echo git push -u origin main
echo.
echo Enable GitHub Pages in repository settings:
echo Settings → Pages → Source: GitHub Actions
pause