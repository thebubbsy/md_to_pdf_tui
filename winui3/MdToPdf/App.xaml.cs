using MdToPdf.Services;
using MdToPdf.ViewModels;
using Microsoft.UI.Xaml;

namespace MdToPdf;

public partial class App : Application
{
    // Small hand-rolled composition root. A DI container (Microsoft.Extensions.DependencyInjection)
    // is the natural next step once the app grows past a couple of pages/services.
    public static SettingsService Settings { get; } = new();
    public static ThemeCatalog Themes { get; } = new();
    public static RecentFilesService RecentFiles { get; } = new();
    public static MarkdownHtmlService MarkdownHtml { get; } = new();

    // Constructed lazily (after the services above exist) since MainViewModel reads them in its constructor.
    public static MainViewModel ViewModel { get; } = new();

    public static Window MainAppWindow { get; private set; } = null!;

    public App()
    {
        InitializeComponent();
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        MainAppWindow = new MainWindow();
        MainAppWindow.Activate();
    }
}
