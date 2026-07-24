function powerworld_to_dataset(input_xlsx, output_basename)
% POWERWORLD_TO_DATASET  Convert a PowerWorld TS time-point export to a dataset.
%
%   powerworld_to_dataset(INPUT_XLSX, OUTPUT_BASENAME) reads the
%   "TSTimePointResult" sheet from INPUT_XLSX, splits it into six 118-column
%   blocks (V pu, gen MW, gen Mvar, load MW, load Mvar, V angle rad), computes
%   per-bus net P/Q on a 100 MVA base, and writes:
%       <OUTPUT_BASENAME>.csv  -- [Pi/100  Qi/100  Vm  Va_rad]
%       <OUTPUT_BASENAME>.mat  -- features=[Pi/100 Qi/100], labels=[Vm Va_rad]
%
%   With no arguments, defaults to ('raw_export.xlsx', 'dataset') in the
%   current working directory.

    if nargin < 1 || isempty(input_xlsx)
        input_xlsx = 'raw_export.xlsx';
    end
    if nargin < 2 || isempty(output_basename)
        output_basename = 'dataset';
    end

    ieee = 118;
    sheetname = 'TSTimePointResult';

    data = readmatrix(input_xlsx, 'Sheet', sheetname);
    data(1:2, :) = [];
    data(:, 1)   = [];

    num_cols   = size(data, 2);
    num_arrays = ceil(num_cols / ieee);
    arrays     = cell(1, num_arrays);
    for i = 1:num_arrays
        c0 = (i - 1) * ieee + 1;
        c1 = min(i * ieee, num_cols);
        arrays{i} = data(:, c0:c1);
    end

    bus_vpu      = arrays{1};
    bus_genMW    = arrays{2};
    bus_genMvar  = arrays{3};
    bus_loadMW   = arrays{4};
    bus_loadMvar = arrays{5};
    bus_vang_rad = arrays{6};

    bus_netPi = bus_genMW   - bus_loadMW;
    bus_netQi = bus_genMvar - bus_loadMvar;

    features = [bus_netPi ./ 100, bus_netQi ./ 100];
    labels   = [bus_vpu,           bus_vang_rad];

    writematrix([features, labels], [output_basename, '.csv']);
    save([output_basename, '.mat'], 'features', 'labels');
end
