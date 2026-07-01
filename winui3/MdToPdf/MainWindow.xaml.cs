using Microsoft.UI.Xaml;

namespace MdToPdf;

// TEMPORARY minimal version for bisecting a runtime XamlParseException in InitializeComponent().
public sealed partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        Title = "MDPDFM Pro";
    }
}
