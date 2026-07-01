using MdToPdf.ViewModels;
using Microsoft.UI.Xaml.Controls;

namespace MdToPdf.Views;

public sealed partial class EditorView : UserControl
{
    public MainViewModel ViewModel => App.ViewModel;

    public EditorView()
    {
        InitializeComponent();
        DataContext = ViewModel;
    }
}
