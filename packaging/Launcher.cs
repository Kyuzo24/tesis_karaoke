using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;
using System.Reflection;

[assembly: AssemblyTitle("Karaoke Studio")]
[assembly: AssemblyVersion("1.0.2.0")]
[assembly: AssemblyFileVersion("1.0.2.0")]

class Launcher {
    [STAThread]
    static void Main() {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        try {
            var start = new ProcessStartInfo {
                FileName = Path.Combine(root, "runtime", "audio", "pythonw.exe"),
                Arguments = "\"" + Path.Combine(root, "launch.py") + "\"",
                WorkingDirectory = root,
                UseShellExecute = false,
                CreateNoWindow = true
            };
            start.EnvironmentVariables.Remove("PYTHONPATH");
            start.EnvironmentVariables.Remove("PYTHONHOME");
            start.EnvironmentVariables["PYTHONNOUSERSITE"] = "1";
            Process.Start(start);
        } catch (Exception error) {
            MessageBox.Show("No se pudo iniciar Karaoke Studio.\n" + error.Message,
                            "Karaoke Studio", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
