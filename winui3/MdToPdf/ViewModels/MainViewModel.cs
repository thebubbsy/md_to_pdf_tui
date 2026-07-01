using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using MdToPdf.Models;
using MdToPdf.Services;
using Microsoft.UI.Xaml.Controls;

namespace MdToPdf.ViewModels;

public sealed partial class MainViewModel : ObservableObject
{
    private readonly SettingsService _settingsService = App.Settings;
    private readonly RecentFilesService _recentFilesService = App.RecentFiles;
    private readonly MarkdownHtmlService _markdownHtml = App.MarkdownHtml;
    private readonly ThemeCatalog _themes = App.Themes;
    private readonly PdfExportService _pdfExport = new();
    private readonly DocxExportService _docxExport = new();

    private CancellationTokenSource? _conversionCts;

    [ObservableProperty] private string _inputFilePath = string.Empty;
    [ObservableProperty] private string _outputFolder;
    [ObservableProperty] private string _selectedThemeName;
    [ObservableProperty] private int _contentWidth;
    [ObservableProperty] private bool _a4FixedWidth;
    [ObservableProperty] private bool _unlimitedHeight;
    [ObservableProperty] private bool _usePasteSource;
    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(WordCountText))]
    private string _pastedMarkdown = string.Empty;

    public string WordCountText
    {
        get
        {
            var words = PastedMarkdown.Split(new[] { ' ', '\n', '\t', '\r' }, StringSplitOptions.RemoveEmptyEntries).Length;
            return $"{words} words · {PastedMarkdown.Length} chars";
        }
    }
    [ObservableProperty] private string _statusText = "Ready.";
    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(IsNotBusy))]
    private bool _isBusy;
    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(HasOutput))]
    private string? _lastOutputPath;

    public bool IsNotBusy => !IsBusy;
    public bool HasOutput => !string.IsNullOrEmpty(LastOutputPath);

    public ObservableCollection<string> ThemeNames { get; }
    public ObservableCollection<string> RecentFiles { get; } = new();

    public MainViewModel()
    {
        var settings = _settingsService.Current;
        _outputFolder = settings.OutputFolder;
        _selectedThemeName = settings.Theme;
        _contentWidth = settings.ContentWidth;
        _a4FixedWidth = settings.A4FixedWidth;
        _unlimitedHeight = settings.UnlimitedHeight;

        ThemeNames = new ObservableCollection<string>(_themes.All.Select(t => t.Name));
        foreach (var f in _recentFilesService.Load()) RecentFiles.Add(f);
    }

    partial void OnOutputFolderChanged(string value) { _settingsService.Current.OutputFolder = value; _settingsService.Save(); }
    partial void OnSelectedThemeNameChanged(string value) { _settingsService.Current.Theme = value; _settingsService.Save(); }
    partial void OnContentWidthChanged(int value) { _settingsService.Current.ContentWidth = value; _settingsService.Save(); }
    partial void OnA4FixedWidthChanged(bool value) { _settingsService.Current.A4FixedWidth = value; _settingsService.Save(); }
    partial void OnUnlimitedHeightChanged(bool value) { _settingsService.Current.UnlimitedHeight = value; _settingsService.Save(); }

    public ThemeDefinition CurrentTheme => _themes.GetOrDefault(SelectedThemeName);

    public string BuildPreviewHtml(string markdown) => _markdownHtml.Render(markdown, _settingsService.Current, CurrentTheme);

    [RelayCommand]
    private void LoadRecent(string path)
    {
        InputFilePath = path;
        UsePasteSource = false;
    }

    [RelayCommand]
    private void CancelConversion()
    {
        // Best-effort: CoreWebView2.PrintToPdfAsync has no CancellationToken overload, so this
        // resets the UI immediately rather than truly aborting an in-flight WebView2 call — the
        // file may still be written a moment later. Good enough for "let me try something else
        // without waiting"; a hard-abort would need dropping to the CDP-level printing API.
        _conversionCts?.Cancel();
        StatusText = "Cancelled.";
        IsBusy = false;
    }

    public async Task ConvertToPdfAsync(WebView2 webView)
    {
        var (markdown, sourceLabel) = ResolveSource();
        if (markdown is null) return;

        await RunConversionAsync("PDF", async ct =>
        {
            var html = BuildPreviewHtml(markdown);
            var outPath = ResolveOutputPath(sourceLabel, "pdf");
            await _pdfExport.ExportAsync(webView, html, outPath, _settingsService.Current);
            LastOutputPath = outPath;
            if (!UsePasteSource) TrackRecent(InputFilePath);
            StatusText = $"PDF export done: {outPath}";
        });
    }

    public async Task ConvertToDocxAsync()
    {
        var (markdown, sourceLabel) = ResolveSource();
        if (markdown is null) return;

        await RunConversionAsync("DOCX", async ct =>
        {
            var outPath = ResolveOutputPath(sourceLabel, "docx");
            await _docxExport.ExportAsync(markdown, outPath, _settingsService.Current);
            LastOutputPath = outPath;
            if (!UsePasteSource) TrackRecent(InputFilePath);
            StatusText = $"DOCX export done: {outPath}";
        });
    }

    private async Task RunConversionAsync(string kind, Func<CancellationToken, Task> work)
    {
        _conversionCts = new CancellationTokenSource();
        IsBusy = true;
        StatusText = $"Converting to {kind}...";
        try
        {
            await work(_conversionCts.Token);
        }
        catch (OperationCanceledException)
        {
            StatusText = "Cancelled.";
        }
        catch (Exception ex)
        {
            StatusText = $"Error: {ex.Message}";
        }
        finally
        {
            IsBusy = false;
        }
    }

    private (string? Markdown, string SourceLabel) ResolveSource()
    {
        if (UsePasteSource)
        {
            if (string.IsNullOrWhiteSpace(PastedMarkdown))
            {
                StatusText = "Paste area is empty.";
                return (null, string.Empty);
            }
            return (PastedMarkdown, $"pasted_export_{Guid.NewGuid().ToString()[..8]}");
        }

        if (string.IsNullOrWhiteSpace(InputFilePath) || !File.Exists(InputFilePath))
        {
            StatusText = "Please select a valid Markdown file first.";
            return (null, string.Empty);
        }

        return (File.ReadAllText(InputFilePath), Path.GetFileNameWithoutExtension(InputFilePath));
    }

    private string ResolveOutputPath(string sourceLabel, string extension)
    {
        var folder = string.IsNullOrWhiteSpace(OutputFolder)
            ? (UsePasteSource ? _settingsService.Current.OutputFolder : Path.GetDirectoryName(InputFilePath)!)
            : OutputFolder;
        Directory.CreateDirectory(folder);
        return Path.Combine(folder, $"{sourceLabel}.{extension}");
    }

    private void TrackRecent(string path)
    {
        var updated = _recentFilesService.AddToRecent(path);
        RecentFiles.Clear();
        foreach (var f in updated) RecentFiles.Add(f);
    }
}
