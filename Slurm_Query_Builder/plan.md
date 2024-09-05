**Web App Name:** SLURM Query Builder

**Rephrased Requirements:**
Create a web application that allows users to select various SLURM resources and parameters through a user-friendly interface. Upon selecting the desired options, the user can generate a corresponding SLURM bash command by clicking a "Generate Query" button.

**User Interface Elements:**
1. **Header:**
   - Title: "SLURM Query Builder"
   - Brief description or instructions.

2. **Resource Selection Section:**
   - **Job Name Input:**
     - Text input field for specifying the job name.
   - **Partition Selection:**
     - Dropdown menu to select the partition.
   - **Number of Nodes:**
     - Number input field to specify the number of nodes.
   - **Number of Tasks:**
     - Number input field to specify the number of tasks.
   - **Memory Allocation:**
     - Number input field with a dropdown for units (MB, GB).
   - **Time Limit:**
     - Time input field (HH:MM:SS) to specify the job duration.
   - **Output File:**
     - Text input field for specifying the output file name.
   - **Error File:**
     - Text input field for specifying the error file name.
   - **Email Notifications:**
     - Checkbox to enable email notifications.
     - Email input field for specifying the email address.
   - **Additional Parameters:**
     - Text input field for any additional SLURM parameters.

3. **Generate Query Button:**
   - A button labeled "Generate Query" to create the SLURM bash command based on the selected options.

4. **Generated Query Display:**
   - A text area or code block to display the generated SLURM command.
   - A "Copy to Clipboard" button to easily copy the generated command.

**Use Cases:**
1. **User Inputs Job Details:**
   - The user enters the job name, selects the partition, specifies the number of nodes, tasks, memory, and time limit.

2. **User Configures Output and Error Files:**
   - The user specifies the output and error file names.

3. **User Enables Email Notifications:**
   - The user checks the box for email notifications and provides an email address.

4. **User Adds Additional Parameters:**
   - The user enters any additional SLURM parameters in the provided text field.

5. **User Generates SLURM Command:**
   - The