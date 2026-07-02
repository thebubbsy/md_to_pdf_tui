using System.ComponentModel;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Media;

namespace MdToPdf;

public sealed partial class MainWindow : Window
{
    private static readonly HashSet<string> PreviewAffectingProperties = new()
    {
        nameof(ViewModels.MainViewModel.PastedMarkdown),
        nameof(ViewModels.MainViewModel.InputFilePath),
        nameof(ViewModels.MainViewModel.UsePasteSource),
        nameof(ViewModels.MainViewModel.SelectedThemeName),
        nameof(ViewModels.MainViewModel.ContentWidth),
    };

    public MainWindow()
    {
        InitializeComponent();

        Title = "MDPDFM Pro";
        SystemBackdrop = new MicaBackdrop();
        ExtendsContentIntoTitleBar = true;
        SetTitleBar(AppTitleBar);

        ConvertPanel.PreviewWebView = PreviewWebView;

        App.ViewModel.PropertyChanged += OnViewModelPropertyChanged;

        _ = InitializePreviewAsync();
    }

    private async void OnViewModelPropertyChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName is not null && PreviewAffectingProperties.Contains(e.PropertyName))
        {
            await RefreshPreviewAsync();
        }
    }

    private async Task InitializePreviewAsync()
    {
        await PreviewWebView.EnsureCoreWebView2Async();
        await RefreshPreviewAsync();
    }

    private async Task RefreshPreviewAsync()
    {
        if (PreviewWebView.CoreWebView2 is null) return;

        var vm = App.ViewModel;
        string markdown;
        if (vm.UsePasteSource)
        {
            markdown = vm.PastedMarkdown;
        }
        else if (!string.IsNullOrWhiteSpace(vm.InputFilePath) && File.Exists(vm.InputFilePath))
        {
            markdown = await File.ReadAllTextAsync(vm.InputFilePath);
        }
        else
        {
            markdown = "# MDPDFM Pro\n\nSelect a file or switch to **Paste & Preview** to get started.";
        }

        var html = vm.BuildPreviewHtml(markdown);
        PreviewWebView.CoreWebView2.NavigateToString(html);
    }
}
