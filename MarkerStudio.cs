using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace MarkerStudio
{
    static class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string pythonExe = Path.Combine(baseDir, ".venv", "Scripts", "pythonw.exe");
                string scriptPath = Path.Combine(baseDir, "marker_gui_app.py");

                if (!File.Exists(pythonExe))
                {
                    pythonExe = Path.Combine(baseDir, ".venv", "Scripts", "python.exe");
                }

                if (!File.Exists(pythonExe))
                {
                    MessageBox.Show(
                        "Ambiente virtuale Python (.venv) non trovato in:\n" + Path.Combine(baseDir, ".venv"),
                        "Marker Studio - Errore",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return;
                }

                if (!File.Exists(scriptPath))
                {
                    MessageBox.Show(
                        "File marker_gui_app.py non trovato in:\n" + scriptPath,
                        "Marker Studio - Errore",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return;
                }

                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = pythonExe;

                string arguments = "\"" + scriptPath + "\"";
                if (args.Length > 0)
                {
                    for (int i = 0; i < args.Length; i++)
                    {
                        arguments += " \"" + args[i] + "\"";
                    }
                }

                psi.Arguments = arguments;
                psi.WorkingDirectory = baseDir;
                psi.UseShellExecute = false;
                psi.CreateNoWindow = true;

                Process.Start(psi);
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    "Errore durante l'avvio di Marker Studio:\n" + ex.Message,
                    "Marker Studio",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
            }
        }
    }
}
