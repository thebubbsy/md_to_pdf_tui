using MdToPdf.Models;

namespace MdToPdf.Services;

// NOT IMPLEMENTED — this is a genuine design decision, not busywork, so it's left for you rather
// than guessed at. The Python app shells out to `pandoc` (see generate_docx_core in
// md_to_pdf_tui.py), which is simple but requires a system-installed pandoc binary and makes
// Mermaid diagrams a screenshot-and-splice step (see MermaidRenderService.cs).
//
// Two real options for this port:
//   1) Shell out to pandoc, same as Python (Process.Start("pandoc", ...)). Fastest to build,
//      identical output to the Python app, but re-inherits the external-dependency problem noted
//      in docs/FEATURE_REPORT.md.
//   2) Generate the .docx natively with DocumentFormat.OpenXml (or the higher-level
//      "Open-Xml-PowerTools"/"DocX" community libraries). Zero external deps, but you own the
//      Markdown-AST-to-OOXML mapping yourself (headings, tables, GitHub alert boxes as colored
//      shaded paragraphs, embedded diagram images).
//
// Whichever you pick, MarkdownHtmlService.Render() already gives you themed HTML for option 1,
// and Markdig's MarkdownDocument AST (Markdown.Parse(text, pipeline)) is the natural input for
// option 2.
public sealed class DocxExportService
{
    public Task ExportAsync(string markdown, string docxPath, AppSettings settings) =>
        throw new NotImplementedException(
            "DOCX export is a stubbed design decision — see the comment at the top of DocxExportService.cs.");
}
