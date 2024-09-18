
de: {
    name: "Deutsch",
    translations: {
        appTitle: "PDF-Forschungszusammenfassung",
        uploadPDF: "PDF hochladen",
        summarize: "Zusammenfassen",
        lollmsConfig: "Lollms-Konfiguration",
        temperature: "Temperatur:",
        maxTokens: "Max. Token:",
        saveConfig: "Konfiguration speichern",
        summary: "Zusammenfassung",
        contribution: "Beitragssynthese:",
        quantitativeResults: "Quantitative Ergebnisse:",
        footer: "PDF-Forschungszusammenfassung © 2023 | Version 1.0",
        copy: "Kopieren",
        exportMarkdown: "Als Markdown exportieren",
        exportHtml: "Als HTML exportieren"
    },
    promptTranslations: {
        summarizePrompt: "Sie sind ein Zusammenfasser von Forschungsarbeiten. Analysieren Sie den folgenden PDF-Inhalt und erstellen Sie eine Zusammenfassung in zwei Teilen:\n1. Eine Synthese des Beitrags der Arbeit\n2. Die quantitativen Ergebnisse der Arbeit\n\nThe answer must be a html <div> tag with the two sections rendered as html. You can use tailwindcss for styling.\n\nHier ist der PDF-Inhalt:\n{pdfContent}\n\nBitte erstellen Sie die Zusammenfassung."
    }
},
it: {
    name: "Italiano",
    translations: {
        appTitle: "Riassunto Ricerca PDF",
        uploadPDF: "Carica PDF",
        summarize: "Riassumi",
        lollmsConfig: "Configurazione Lollms",
        temperature: "Temperatura:",
        maxTokens: "Token Massimi:",
        saveConfig: "Salva Configurazione",
        summary: "Riassunto",
        contribution: "Sintesi del Contributo:",
        quantitativeResults: "Risultati Quantitativi:",
        footer: "Riassunto Ricerca PDF © 2023 | Versione 1.0",
        copy: "Copia",
        exportMarkdown: "Esporta in Markdown",
        exportHtml: "Esporta in HTML"
    },
    promptTranslations: {
        summarizePrompt: "Sei un riassuntore di articoli di ricerca. Analizza il seguente contenuto PDF e fornisci un riassunto in due parti:\n1. Una sintesi del contributo dell'articolo\n2. I risultati quantitativi dell'articolo\n\nThe answer must be a html <div> tag with the two sections rendered as html. You can use tailwindcss for styling.\n\nEcco il contenuto del PDF:\n{pdfContent}\n\nPer favore, fornisci il riassunto."
    }
}