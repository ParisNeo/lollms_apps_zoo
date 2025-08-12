// lollms-code-patcher/dist/script.js
document.addEventListener('DOMContentLoaded', () => {
    const editorConfig = (mode, readOnly = false) => ({
        lineNumbers: true,
        theme: 'material-darker',
        mode: mode,
        readOnly: readOnly,
        lineWrapping: true,
    });

    const originalEditor = CodeMirror.fromTextArea(document.getElementById('original-code'), editorConfig('python'));
    const patchEditor = CodeMirror.fromTextArea(document.getElementById('patch-text'), editorConfig('diff'));
    const patchedEditor = CodeMirror.fromTextArea(document.getElementById('patched-code'), editorConfig('python', true));

    const patchButton = document.getElementById('patch-button');
    const statusMessage = document.getElementById('status-message');

    // --- DEFINITIVE FIX: Ensure example strings end with a newline ---
    const exampleCode =
`def fibonacci(n):
    """Return the nth fibonacci number."""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)
`; // A newline is now implicitly here

    const examplePatch =
`--- a/original.py
+++ b/new.py
@@ -1,8 +1,12 @@
+memo = {}
 def fibonacci(n):
     """Return the nth fibonacci number."""
+    if n in memo:
+        return memo[n]
     if n <= 0:
         return 0
     elif n == 1:
         return 1
     else:
-        return fibonacci(n-1) + fibonacci(n-2)
+        result = fibonacci(n-1) + fibonacci(n-2)
+        memo[n] = result
+        return result
`; // A newline is now implicitly here

    originalEditor.setValue(exampleCode);
    patchEditor.setValue(examplePatch);

    patchButton.addEventListener('click', async () => {
        // We still use getValue('\n') to handle user input correctly
        const originalCode = originalEditor.getValue('\n');
        const patchText = patchEditor.getValue('\n');

        if (!originalCode.trim() || !patchText.trim()) {
            setStatus('Please provide both original code and a patch.', 'error');
            return;
        }
        patchButton.disabled = true;
        setStatus('Applying patch...', 'info');
        patchedEditor.setValue('');

        try {
            const response = await fetch('/patch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    original_code: originalCode,
                    patch_text: patchText,
                }),
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.detail || 'An unknown error occurred.');
            }
            patchedEditor.setValue(result.patched_code);
            setStatus('Patch applied successfully!', 'success');
        } catch (error) {
            console.error('Patching failed:', error);
            setStatus(`Error: ${error.message}`, 'error');
        } finally {
            patchButton.disabled = false;
        }
    });

    function setStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = type;
    }
});