//+------------------------------------------------------------------+
//|                                                    AllBestEA.mq4 |
//|                        Copyright 2024, TradingView Integration  |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, TradingView Integration"
#property link      ""
#property version   "1.00"
#property strict

//--- Input parameters
input string SignalsDirectory = "/Users/pasith/DevFlutter/crypto_trading_system/crypto_trading_backend/mt4_signals/"; // Signals directory path (relative to MQL4\Files\)
input double DefaultLotSize = 0.01;             // Default lot size if not specified in signal
input double MaxLotSize = 1.0;                  // Maximum allowed lot size
input int MagicNumber = 123456;                 // Magic number for orders
input int MaxSignalAge = 300;                   // Maximum signal age in seconds (5 minutes)
input bool EnableLogging = true;                // Enable detailed logging
input int ScanInterval = 1000;                  // Signal scan interval in milliseconds
input double MaxSpread = 3.0;                   // Maximum allowed spread in points
input bool ValidateSymbols = true;              // Validate if symbol exists before trading

//--- Global variables
string g_signalsPath;
datetime g_lastScanTime = 0;
int g_processedSignals = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    // Initialize signals directory path
    g_signalsPath = SignalsDirectory;
    
    // Create directory if it doesn't exist
    if(!CreateDirectory(g_signalsPath))
    {
        Print("Warning: Could not create signals directory: " + g_signalsPath);
    }
    
    Print("=== AllBestEA Initialized ===");
    Print("Signals Directory: " + g_signalsPath);
    Print("Magic Number: " + IntegerToString(MagicNumber));
    Print("Default Lot Size: " + DoubleToString(DefaultLotSize, 2));
    Print("Max Lot Size: " + DoubleToString(MaxLotSize, 2));
    Print("Scan Interval: " + IntegerToString(ScanInterval) + "ms");
    Print("================================");
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("=== AllBestEA Deinitialized ===");
    Print("Total Signals Processed: " + IntegerToString(g_processedSignals));
    Print("Reason: " + IntegerToString(reason));
    Print("================================");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Scan for new signals periodically
    if(GetTickCount() - g_lastScanTime > ScanInterval)
    {
        ScanForSignals();
        g_lastScanTime = GetTickCount();
    }
}

//+------------------------------------------------------------------+
//| Scan for new signal files                                       |
//+------------------------------------------------------------------+
void ScanForSignals()
{
    string fileName;
    long searchHandle = FileFindFirst(g_signalsPath + "\\*.json", fileName);
    
    if(searchHandle == INVALID_HANDLE)
    {
        return; // No files found
    }
    
    do
    {
        string filePath = g_signalsPath + "\\" + fileName;
        
        if(EnableLogging)
            Print("Found signal file: " + fileName);
        
        ProcessSignalFile(filePath);
        
    } while(FileFindNext(searchHandle, fileName));
    
    FileFindClose(searchHandle);
}

//+------------------------------------------------------------------+
//| Process individual signal file                                  |
//+------------------------------------------------------------------+
void ProcessSignalFile(string filePath)
{
    int fileHandle = FileOpen(filePath, FILE_READ | FILE_TXT);
    
    if(fileHandle == INVALID_HANDLE)
    {
        if(EnableLogging)
            Print("ERROR: Could not open signal file: " + filePath);
        return;
    }
    
    // Read entire file content
    string jsonContent = "";
    while(!FileIsEnding(fileHandle))
    {
        jsonContent += FileReadString(fileHandle);
    }
    FileClose(fileHandle);
    
    if(EnableLogging)
        Print("Signal file content: " + jsonContent);
    
    // Parse JSON signal
    SignalData signal;
    if(ParseSignalJSON(jsonContent, signal))
    {
        // Validate signal age
        if(!IsSignalValid(signal))
        {
            if(EnableLogging)
                Print("Signal is too old or invalid, skipping: " + filePath);
            DeleteSignalFile(filePath);
            return;
        }
        
        // Process the trading signal
        if(ExecuteTradingSignal(signal))
        {
            g_processedSignals++;
            Print("Successfully processed signal #" + IntegerToString(g_processedSignals) + 
                  " for " + signal.symbol + " " + signal.action);
        }
        else
        {
            Print("Failed to execute signal for " + signal.symbol + " " + signal.action);
        }
    }
    else
    {
        Print("ERROR: Failed to parse signal JSON: " + filePath);
    }
    
    // Delete processed signal file
    DeleteSignalFile(filePath);
}

//+------------------------------------------------------------------+
//| Signal data structure                                            |
//+------------------------------------------------------------------+
struct SignalData
{
    string timestamp;
    string symbol;
    string originalSymbol;
    string action;          // BUY or SELL
    double entryPrice;
    double tpPrice;
    double slPrice;
    double lotSize;
    int magicNumber;
    string message;
    bool processed;
};

//+------------------------------------------------------------------+
//| Parse JSON signal content                                        |
//+------------------------------------------------------------------+
bool ParseSignalJSON(string jsonContent, SignalData &signal)
{
    // Simple JSON parsing for signal fields
    // Note: MQL4 doesn't have built-in JSON parsing, so we use string operations
    
    signal.symbol = ExtractJSONValue(jsonContent, "symbol");
    signal.originalSymbol = ExtractJSONValue(jsonContent, "original_symbol");
    signal.action = ExtractJSONValue(jsonContent, "action");
    signal.timestamp = ExtractJSONValue(jsonContent, "timestamp");
    signal.message = ExtractJSONValue(jsonContent, "message");
    
    // Parse numeric values
    string entryStr = ExtractJSONValue(jsonContent, "entry_price");
    string tpStr = ExtractJSONValue(jsonContent, "tp_price");
    string slStr = ExtractJSONValue(jsonContent, "sl_price");
    string lotStr = ExtractJSONValue(jsonContent, "lot_size");
    string magicStr = ExtractJSONValue(jsonContent, "magic_number");
    
    signal.entryPrice = StringToDouble(entryStr);
    signal.tpPrice = StringToDouble(tpStr);
    signal.slPrice = StringToDouble(slStr);
    signal.lotSize = StringToDouble(lotStr);
    signal.magicNumber = StringToInteger(magicStr);
    
    // Validate required fields
    if(signal.symbol == "" || signal.action == "")
    {
        return false;
    }
    
    // Validate lot size
    if(signal.lotSize <= 0)
    {
        signal.lotSize = DefaultLotSize;
    }
    else if(signal.lotSize > MaxLotSize)
    {
        signal.lotSize = MaxLotSize;
    }
    
    // Set magic number if not provided
    if(signal.magicNumber <= 0)
    {
        signal.magicNumber = MagicNumber;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Extract value from JSON string                                   |
//+------------------------------------------------------------------+
string ExtractJSONValue(string json, string key)
{
    string searchKey = "\"" + key + "\"";
    int keyPos = StringFind(json, searchKey);
    
    if(keyPos == -1)
        return "";
    
    // Find the colon after the key
    int colonPos = StringFind(json, ":", keyPos);
    if(colonPos == -1)
        return "";
    
    // Find the start of the value (skip whitespace and quotes)
    int valueStart = colonPos + 1;
    while(valueStart < StringLen(json) && 
          (StringGetCharacter(json, valueStart) == ' ' || 
           StringGetCharacter(json, valueStart) == '"'))
    {
        valueStart++;
    }
    
    // Find the end of the value
    int valueEnd = valueStart;
    bool inQuotes = (StringGetCharacter(json, valueStart - 1) == '"');
    
    if(inQuotes)
    {
        // Find closing quote
        while(valueEnd < StringLen(json) && StringGetCharacter(json, valueEnd) != '"')
        {
            valueEnd++;
        }
    }
    else
    {
        // Find comma or closing brace
        while(valueEnd < StringLen(json) && 
              StringGetCharacter(json, valueEnd) != ',' && 
              StringGetCharacter(json, valueEnd) != '}' &&
              StringGetCharacter(json, valueEnd) != '\n')
        {
            valueEnd++;
        }
        
        // Trim whitespace from end
        while(valueEnd > valueStart && StringGetCharacter(json, valueEnd - 1) == ' ')
        {
            valueEnd--;
        }
    }
    
    return StringSubstr(json, valueStart, valueEnd - valueStart);
}

//+------------------------------------------------------------------+
//| Validate signal age and data                                     |
//+------------------------------------------------------------------+
bool IsSignalValid(SignalData &signal)
{
    // Check signal age (simple validation - you may want to implement proper datetime parsing)
    // For now, we'll assume signals are valid if they have required fields
    
    if(signal.symbol == "" || signal.action == "")
        return false;
    
    // Validate symbol exists (if enabled)
    if(ValidateSymbols)
    {
        if(MarketInfo(signal.symbol, MODE_POINT) <= 0)
        {
            Print("WARNING: Symbol " + signal.symbol + " not found or not available");
            return false;
        }
    }
    
    // Check spread
    double spread = MarketInfo(signal.symbol, MODE_SPREAD);
    if(spread > MaxSpread)
    {
        Print("WARNING: Spread too high for " + signal.symbol + ": " + DoubleToString(spread, 1));
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Execute trading signal                                           |
//+------------------------------------------------------------------+
bool ExecuteTradingSignal(SignalData &signal)
{
    // Check if market is open
    if(!IsTradeAllowed())
    {
        Print("WARNING: Trading not allowed at this time");
        return false;
    }
    
    // Normalize lot size
    double lotSize = NormalizeLots(signal.symbol, signal.lotSize);
    
    // Determine order type
    int orderType = (signal.action == "BUY") ? OP_BUY : OP_SELL;
    
    // Get current price
    double price = (orderType == OP_BUY) ? MarketInfo(signal.symbol, MODE_ASK) : 
                                          MarketInfo(signal.symbol, MODE_BID);
    
    // Normalize TP and SL prices
    double tp = NormalizePrice(signal.symbol, signal.tpPrice);
    double sl = NormalizePrice(signal.symbol, signal.slPrice);
    
    // Validate TP/SL
    if(!ValidateTPSL(signal.symbol, orderType, price, tp, sl))
    {
        Print("WARNING: Invalid TP/SL levels for " + signal.symbol);
        // Continue without TP/SL if they are invalid
        tp = 0;
        sl = 0;
    }
    
    // Place order
    int ticket = OrderSend(
        signal.symbol,           // Symbol
        orderType,               // Order type
        lotSize,                 // Lot size
        price,                   // Price
        3,                       // Slippage
        sl,                      // Stop loss
        tp,                      // Take profit
        "TradingView: " + signal.message, // Comment
        signal.magicNumber,      // Magic number
        0,                       // Expiration
        (orderType == OP_BUY) ? clrBlue : clrRed // Color
    );
    
    if(ticket > 0)
    {
        Print("SUCCESS: Order placed - Ticket: " + IntegerToString(ticket) + 
              ", Symbol: " + signal.symbol + 
              ", Action: " + signal.action + 
              ", Lot Size: " + DoubleToString(lotSize, 2) + 
              ", Price: " + DoubleToString(price, Digits) +
              ", TP: " + DoubleToString(tp, Digits) + 
              ", SL: " + DoubleToString(sl, Digits));
        return true;
    }
    else
    {
        int error = GetLastError();
        Print("ERROR: Failed to place order - Error: " + IntegerToString(error) + 
              " - " + ErrorDescription(error));
        return false;
    }
}

//+------------------------------------------------------------------+
//| Normalize lot size according to symbol specifications           |
//+------------------------------------------------------------------+
double NormalizeLots(string symbol, double lots)
{
    double minLot = MarketInfo(symbol, MODE_MINLOT);
    double maxLot = MarketInfo(symbol, MODE_MAXLOT);
    double lotStep = MarketInfo(symbol, MODE_LOTSTEP);
    
    if(lots < minLot)
        lots = minLot;
    else if(lots > maxLot)
        lots = maxLot;
    
    // Round to lot step
    lots = MathRound(lots / lotStep) * lotStep;
    
    return lots;
}

//+------------------------------------------------------------------+
//| Normalize price according to symbol specifications              |
//+------------------------------------------------------------------+
double NormalizePrice(string symbol, double price)
{
    if(price <= 0)
        return 0;
    
    double point = MarketInfo(symbol, MODE_POINT);
    int digits = (int)MarketInfo(symbol, MODE_DIGITS);
    
    return NormalizeDouble(price, digits);
}

//+------------------------------------------------------------------+
//| Validate Take Profit and Stop Loss levels                       |
//+------------------------------------------------------------------+
bool ValidateTPSL(string symbol, int orderType, double price, double tp, double sl)
{
    if(tp <= 0 && sl <= 0)
        return true; // No TP/SL specified
    
    double minDistance = MarketInfo(symbol, MODE_STOPLEVEL) * MarketInfo(symbol, MODE_POINT);
    
    if(orderType == OP_BUY)
    {
        if(tp > 0 && tp <= price + minDistance)
            return false;
        if(sl > 0 && sl >= price - minDistance)
            return false;
    }
    else // OP_SELL
    {
        if(tp > 0 && tp >= price - minDistance)
            return false;
        if(sl > 0 && sl <= price + minDistance)
            return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Delete processed signal file                                    |
//+------------------------------------------------------------------+
void DeleteSignalFile(string filePath)
{
    if(FileDelete(filePath))
    {
        if(EnableLogging)
            Print("Deleted processed signal file: " + filePath);
    }
    else
    {
        if(EnableLogging)
            Print("WARNING: Could not delete signal file: " + filePath);
    }
}

//+------------------------------------------------------------------+
//| Create directory                                                |
//+------------------------------------------------------------------+
bool CreateDirectory(string path)
{
    // Check if directory already exists
    long handle = FileFindFirst(path + "\\*", path);
    if(handle != INVALID_HANDLE)
    {
        FileFindClose(handle);
        return true;
    }
    
    // Try to create directory by creating and deleting a temporary file
    string tempFile = path + "\\temp.txt";
    int fileHandle = FileOpen(tempFile, FILE_WRITE | FILE_TXT);
    
    if(fileHandle != INVALID_HANDLE)
    {
        FileWrite(fileHandle, "temp");
        FileClose(fileHandle);
        FileDelete(tempFile);
        return true;
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Get error description                                            |
//+------------------------------------------------------------------+
string ErrorDescription(int errorCode)
{
    switch(errorCode)
    {
        case 0:   return "No error";
        case 1:   return "No error, trade is successful";
        case 2:   return "Common error";
        case 3:   return "Invalid trade parameters";
        case 4:   return "Trade server is busy";
        case 5:   return "Old version of the client terminal";
        case 6:   return "No connection with trade server";
        case 7:   return "Not enough rights";
        case 8:   return "Too frequent requests";
        case 9:   return "Malfunctional trade operation";
        case 64:  return "Account disabled";
        case 65:  return "Invalid account";
        case 128: return "Trade timeout";
        case 129: return "Invalid price";
        case 130: return "Invalid stops";
        case 131: return "Invalid trade volume";
        case 132: return "Market is closed";
        case 133: return "Trade is disabled";
        case 134: return "Not enough money";
        case 135: return "Price changed";
        case 136: return "Off quotes";
        case 137: return "Broker is busy";
        case 138: return "Requote";
        case 139: return "Order is locked";
        case 140: return "Long positions only allowed";
        case 141: return "Too many requests";
        case 145: return "Modification denied because too close to market";
        case 146: return "Trade context is busy";
        case 147: return "Expirations are denied by broker";
        case 148: return "Trade amount is changed by broker";
        default:  return "Unknown error " + IntegerToString(errorCode);
    }
}
