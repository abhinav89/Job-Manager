# Landing page

All eight gallery formats and the CV Studio preview use Reinael Yabut's supplied resume. The source content in `content/reinael-resume.json` is independent of the saved career profile and retains the dates and claims from the provided `Reinael_Yabut CV.pdf`.

Regenerate the shared landing-page and dashboard gallery assets from the repository root:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/build_resume_gallery.py
```

Use the installed CV Tailor Python environment, Tectonic, and Poppler (`pdftoppm` and `pdftotext`). The script uses the real templates, fits the complete typeset resume to one page, and checks every bullet, skills row, and certification before rendering its PNG. Each format's PDF and PNG in both apps' `public/resume-templates/` directories must ship together.

Build and check with `npm --prefix landing run build`, `npm --prefix landing run lint`, and `npm --prefix landing run test:browser`.
