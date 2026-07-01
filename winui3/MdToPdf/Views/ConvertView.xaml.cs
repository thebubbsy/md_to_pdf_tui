using MdToPdf.ViewModels;
using Microsoft.UI.Xaml.Controls;
using Windows.Storage.Pickers;
using WinRT.Interop;

namespace MdToPdf.Views;

public sealed partial class ConvertView : UserControl
{
    // Set by MainWindow after construction — the preview WebView2 lives at the window level so it
    // survives switching between the Convert and Editor tabs. See MainWindow.xaml.cs.
    public WebView2? PreviewWebView { get; set; }

    public MainViewModel ViewModel => App.ViewModel;

    public ConvertView()
    {
        InitializeComponent();
        DataContext = ViewModel;
    }

    private async void OnBrowseFileClick(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        var picker = new FileOpenPicker();
        InitializeWithWindow.Initialize(picker, WindowNative.GetWindowHandle(App.MainAppWindow));
        picker.FileTypeFilter.Add(".md");
        picker.FileTypeFilter.Add(".markdown");
        var file = await picker.PickSingleFileAsync();
        if (file is not null)
        {
            ViewModel.InputFilePath = file.Path;
            ViewModel.UsePasteSource = false;
        }
    }

    private async void OnBrowseFolderClick(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        var picker = new FolderPicker();
        InitializeWithWindow.Initialize(picker, WindowNative.GetWindowHandle(App.MainAppWindow));
        picker.FileTypeFilter.Add("*");
        var folder = await picker.PickSingleFolderAsync();
        if (folder is not null) ViewModel.OutputFolder = folder.Path;
    }

    private void OnRecentSelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (sender is ComboBox { SelectedItem: string path })
        {
            ViewModel.LoadRecentCommand.Execute(path);
        }
    }

    private async void OnConvertPdfClick(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        if (PreviewWebView is null) return;
        await ViewModel.ConvertToPdfAsync(PreviewWebView);
    }

    private async void OnConvertDocxClick(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        await ViewModel.ConvertToDocxAsync();
    }

    private void OnOpenOutputClick(object sender, Microsoft.UI.Xaml.RoutedEventArgs e)
    {
        if (ViewModel.LastOutputPath is { } path && System.IO.File.Exists(path))
        {
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(path) { UseShellExecute = true });
        }
    }
}
