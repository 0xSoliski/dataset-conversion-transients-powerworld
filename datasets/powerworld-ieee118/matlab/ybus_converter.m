% Specify your input file name
filename = 'ybus.xlsx';

% Read data from the Excel file
[~, ~, raw_data] = xlsread(filename);  % raw_data will contain both numbers and strings

% Remove the first two rows and the first column
raw_data(1:2,:) = []; % Remove the first two rows
raw_data(:,1:2) = [];   % Remove the first column

% Initialize Ybus matrix (adjust dimensions as needed)
[rows, cols] = size(raw_data); % Get the number of rows and columns in raw data
Ybus = zeros(rows, cols);  % Initialize Ybus matrix with appropriate size

% Initialize G and B matrices for storing real and imaginary parts
G = zeros(rows, cols);  % Real part (Conductance matrix)
B = zeros(rows, cols);  % Imaginary part (Susceptance matrix)

% Loop over the rows and columns of the raw_data
for i = 1:rows
    for j = 1:cols
        % Check if the value is NaN (and handle accordingly)
        if isnan(raw_data{i, j})
            Ybus(i, j) = 0;  % Set to 0 if NaN
            G(i, j) = 0;  % Set the corresponding G and B to 0
            B(i, j) = 0;
            continue; % Skip the rest of the code for this cell
        end

        % Skip empty cells
        if isempty(raw_data{i, j})
            Ybus(i, j) = 0;  % Set the value to 0 if the cell is empty
            G(i, j) = 0;
            B(i, j) = 0;
            continue; % Skip empty cells
        end

        % Debug: Display cell content and type
        fprintf('Parsing cell (%d, %d): ', i, j);
        disp(raw_data{i, j}); % Display the value in the cell

        % Handle cell content based on type
        if isnumeric(raw_data{i, j})
            % If the value is numeric, directly assign it
            Ybus(i, j) = raw_data{i, j};
            G(i, j) = real(raw_data{i, j}); % Real part to G
            B(i, j) = imag(raw_data{i, j}); % Imaginary part to B
        elseif ischar(raw_data{i, j}) || isstring(raw_data{i, j})
            % If the value is a string (complex number), parse it
            try
                % Clean up the string by removing spaces and parentheses
                val = strrep(raw_data{i, j}, ' ', '');  % Remove spaces
                val = strrep(val, '(', '');  % Remove opening parentheses
                val = strrep(val, ')', '');  % Remove closing parentheses

                % Remove 'j' and append 'i' at the end
                val = strrep(val, 'j', '');  % Remove 'j'
                val = [val, 'i'];  % Append 'i' to the end of the string

                % Debug: Display cleaned string
                fprintf('Cleaned string for parsing: %s\n', val);

                % Parse the string as a complex number
                parsed_value = str2num(val); % Try to parse the value
                if ~isempty(parsed_value)
                    Ybus(i, j) = parsed_value; % Store complex number in Ybus
                    G(i, j) = real(parsed_value); % Store real part in G
                    B(i, j) = imag(parsed_value); % Store imaginary part in B
                else
                    warning('Could not parse cell (%d, %d), defaulting to 0.', i, j);
                    Ybus(i, j) = 0;
                    G(i, j) = 0;
                    B(i, j) = 0;
                end
            catch
                warning('Error parsing cell (%d, %d), defaulting to 0.', i, j);
                Ybus(i, j) = 0;
                G(i, j) = 0;
                B(i, j) = 0;
            end
        else
            % Handle any unsupported types by defaulting to 0
            warning('Unsupported cell type at (%d, %d), defaulting to 0.', i, j);
            Ybus(i, j) = 0;
            G(i, j) = 0;
            B(i, j) = 0;
        end
    end
end

% Save the matrices to CSV
writematrix(G, 'G_matrix.csv', 'Delimiter', ',');
writematrix(B, 'B_matrix.csv', 'Delimiter', ',');

% Display confirmation
fprintf('G and B matrices saved to G_matrix.csv and B_matrix.csv.\n');