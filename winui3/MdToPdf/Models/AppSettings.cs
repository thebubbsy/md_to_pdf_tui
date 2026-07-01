namespace MdToPdf.Models;

public sealed class AppSettings
{
    public string Theme { get; set; } = "GitHub Light";
    public int ContentWidth { get; set; } = 800;
    public bool MermaidEnabled { get; set; } = true;
    public string OutputFolder { get; set; } =
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments));
    public bool UnlimitedHeight { get; set; } = true;
    public bool A4FixedWidth { get; set; } = true;
}
