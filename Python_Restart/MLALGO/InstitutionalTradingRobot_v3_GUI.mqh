//+------------------------------------------------------------------+
//| InstitutionalTradingRobot_v3_GUI.mqh                             |
//| Interactive GUI - Clickable Buttons & Controls                   |
//+------------------------------------------------------------------+

// Forward declarations
void CreateToggleButton(string name, int x, int y, int width, int height, string text, bool initial_state, color col_on, color col_off, string setting_name);
void CreateBigLabel(string name, int x, int y, string text, color clr, int font_size, bool bold);
void UpdateAllButtons();
void UpdateSetting(string setting, bool value);
void CreateColorBox(int index, int x, int y, color clr);
void CreateLegendLabel(int index, int x, int y, string text, color clr, int font_size, bool bold);
void DrawButtonStatus();
void DrawMLStatus();  // ML STATUS PANEL

// ML Action Tracking
struct MLAction
{
    datetime timestamp;
    string action_text;
    color text_color;
    bool was_approved;
};

MLAction ml_action_buffer[20];
int ml_action_count = 0;

// Button structure
struct Button
{
    string name;
    int x;
    int y;
    int width;
    int height;
    string text;
    bool state;         // true = ON, false = OFF
    color color_on;
    color color_off;
    string setting;     // Which setting this controls
};

Button gui_buttons[50];  // Enough for all buttons + future expansion
int button_count = 0;

//+------------------------------------------------------------------+
//| TOGGLE GUI MINIMIZE/MAXIMIZE                                     |
//+------------------------------------------------------------------+
void ToggleGuiMinimize()
{
    g_GuiMinimized = !g_GuiMinimized;

    // Hide/Show all GUI objects except the minimize button
    for(int i = 0; i < button_count; i++)
    {
        // Skip the minimize button itself
        if(StringFind(gui_buttons[i].name, "BTN_MINIMIZE") >= 0)
            continue;

        ObjectSetInteger(0, gui_buttons[i].name, OBJPROP_TIMEFRAMES,
                         g_GuiMinimized ? OBJ_NO_PERIODS : OBJ_ALL_PERIODS);
    }

    // Hide/Show all labels (titles, sections)
    ObjectSetInteger(0, prefix + "GUI_Title", OBJPROP_TIMEFRAMES,
                     g_GuiMinimized ? OBJ_NO_PERIODS : OBJ_ALL_PERIODS);
    ObjectSetInteger(0, prefix + "GUI_Filters", OBJPROP_TIMEFRAMES,
                     g_GuiMinimized ? OBJ_NO_PERIODS : OBJ_ALL_PERIODS);
    ObjectSetInteger(0, prefix + "GUI_SmartMoney", OBJPROP_TIMEFRAMES,
                     g_GuiMinimized ? OBJ_NO_PERIODS : OBJ_ALL_PERIODS);
    ObjectSetInteger(0, prefix + "GUI_ML", OBJPROP_TIMEFRAMES,
                     g_GuiMinimized ? OBJ_NO_PERIODS : OBJ_ALL_PERIODS);
    ObjectSetInteger(0, prefix + "GUI_Visuals", OBJPROP_TIMEFRAMES,
                     g_GuiMinimized ? OBJ_NO_PERIODS : OBJ_ALL_PERIODS);

    // Update minimize button text
    for(int i = 0; i < button_count; i++)
    {
        if(StringFind(gui_buttons[i].name, "BTN_MINIMIZE") >= 0)
        {
            string button_text = g_GuiMinimized ? "☰ SHOW PANEL" : "✕ HIDE PANEL";
            ObjectSetString(0, gui_buttons[i].name, OBJPROP_TEXT, button_text);
            break;
        }
    }

    ChartRedraw();

    if(g_GuiMinimized)
        Print("✓ GUI Panel MINIMIZED - Clean chart view | EA continues running");
    else
        Print("✓ GUI Panel MAXIMIZED - Full controls visible");
}

//+------------------------------------------------------------------+
//| CREATE INTERACTIVE DASHBOARD WITH BUTTONS                        |
//+------------------------------------------------------------------+
void CreateInteractiveDashboard()
{
    int x_start = 20;
    int y_start = 20;               // Start higher for minimize button
    int button_width = 280;
    int button_height = 35;
    int spacing = 5;
    int row = 0;

    button_count = 0;

    // MINIMIZE/MAXIMIZE BUTTON (Very first button at the top)
    CreateToggleButton("BTN_MINIMIZE", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "✕ HIDE PANEL",
                      false, clrDodgerBlue, clrDodgerBlue, "MINIMIZE");
    row++;
    row++;  // Extra spacing after minimize button

    // Title
    CreateBigLabel("GUI_Title", x_start, y_start + row * (button_height + spacing),
                   "═══ INSTITUTIONAL TRADING ROBOT v3.0 ═══",
                   clrWhite, 14, true);

    row++;
    y_start += 50;

    // MODE TOGGLE - BIG AND OBVIOUS
    CreateToggleButton("BTN_MODE", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      g_EnableTrading ? "MODE: AUTO TRADING ✓" : "MODE: INDICATOR ONLY",
                      g_EnableTrading, clrLime, clrOrange, "MODE");
    row++;

    row++; // Spacing

    // SECTION: INSTITUTIONAL FILTERS
    CreateBigLabel("GUI_Filters", x_start, y_start + row * (button_height + spacing),
                   "─── INSTITUTIONAL FILTERS ───", clrAqua, 12, false);
    row++;

    CreateToggleButton("BTN_VOLUME", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Volume Filter",
                      g_UseVolumeFilter, clrLime, clrRed, "VOLUME");
    row++;

    CreateToggleButton("BTN_SPREAD", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Spread Filter",
                      g_UseSpreadFilter, clrLime, clrRed, "SPREAD");
    row++;

    CreateToggleButton("BTN_SLIPPAGE", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Slippage Model",
                      g_UseSlippageModel, clrLime, clrRed, "SLIPPAGE");
    row++;

    CreateToggleButton("BTN_MTF", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Multi-Timeframe Confirm",
                      g_UseMTFConfirmation, clrLime, clrRed, "MTF");
    row++;

    CreateToggleButton("BTN_SESSION", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Session Filter",
                      g_UseSessionFilter, clrLime, clrRed, "SESSION");
    row++;

    CreateToggleButton("BTN_CORRELATION", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Correlation Filter",
                      g_UseCorrelationFilter, clrLime, clrRed, "CORRELATION");
    row++;

    CreateToggleButton("BTN_NEWS", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "News Filter",
                      g_UseNewsFilter, clrLime, clrRed, "NEWS");
    row++;

    CreateToggleButton("BTN_VOLATILITY", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Volatility Adaptation",
                      g_UseVolatilityAdaptation, clrLime, clrRed, "VOLATILITY");
    row++;

    CreateToggleButton("BTN_DYNAMIC_RISK", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Dynamic Risk",
                      g_UseDynamicRisk, clrLime, clrRed, "DYNAMIC_RISK");
    row++;

    CreateToggleButton("BTN_PATTERN_DECAY", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Pattern Decay",
                      g_UsePatternDecay, clrLime, clrRed, "PATTERN_DECAY");
    row++;

    row++; // Spacing

    // SECTION: SMART MONEY
    CreateBigLabel("GUI_SmartMoney", x_start, y_start + row * (button_height + spacing),
                   "─── SMART MONEY CONCEPTS ───", clrAqua, 12, false);
    row++;

    CreateToggleButton("BTN_LIQUIDITY", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Liquidity Sweep",
                      g_UseLiquiditySweep, clrLime, clrRed, "LIQUIDITY");
    row++;

    CreateToggleButton("BTN_RETAIL_TRAP", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Retail Trap Detection",
                      g_UseRetailTrap, clrLime, clrRed, "RETAIL_TRAP");
    row++;

    CreateToggleButton("BTN_OB_INVALID", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Order Block Invalidation",
                      g_UseOrderBlockInvalidation, clrLime, clrRed, "OB_INVALID");
    row++;

    CreateToggleButton("BTN_STRUCTURE", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Market Structure",
                      g_UseMarketStructure, clrLime, clrRed, "STRUCTURE");
    row++;

    row++; // Spacing

    // SECTION: MACHINE LEARNING
    CreateBigLabel("GUI_ML", x_start, y_start + row * (button_height + spacing),
                   "─── MACHINE LEARNING ───", clrAqua, 12, false);
    row++;

    CreateToggleButton("BTN_ML_ENABLE", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "ML System Enable",
                      g_MLEnabled, clrLime, clrRed, "ML_ENABLE");
    row++;

    CreateToggleButton("BTN_PATTERN_TRACK", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Pattern Performance Tracking",
                      g_UsePatternTracking, clrLime, clrRed, "PATTERN_TRACK");
    row++;

    CreateToggleButton("BTN_ADAPTATION", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Parameter Adaptation",
                      g_UseParameterAdaptation, clrLime, clrRed, "ADAPTATION");
    row++;

    CreateToggleButton("BTN_REGIME_STRATEGY", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Regime Strategy",
                      g_UseRegimeStrategy, clrLime, clrRed, "REGIME_STRATEGY");
    row++;

    row++; // Spacing

    // SECTION: VISUAL CONTROLS
    CreateBigLabel("GUI_Visuals", x_start, y_start + row * (button_height + spacing),
                   "─── CHART VISUALS ───", clrYellow, 12, false);
    row++;

    CreateToggleButton("BTN_SHOW_PATTERNS", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Pattern Boxes",
                      g_ShowPatternBoxes, clrLime, clrGray, "SHOW_PATTERNS");
    row++;

    CreateToggleButton("BTN_SHOW_LABELS", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Pattern Labels",
                      g_ShowPatternLabels, clrLime, clrGray, "SHOW_LABELS");
    row++;

    CreateToggleButton("BTN_SHOW_LIQ", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Liquidity Zones",
                      g_ShowLiquidityZones, clrLime, clrGray, "SHOW_LIQ");
    row++;

    CreateToggleButton("BTN_SHOW_FVG", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Fair Value Gaps",
                      g_ShowFVGZones, clrLime, clrGray, "SHOW_FVG");
    row++;

    CreateToggleButton("BTN_SHOW_OB", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Order Blocks",
                      g_ShowOrderBlocks, clrLime, clrGray, "SHOW_OB");
    row++;

    CreateToggleButton("BTN_SHOW_DASH", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Dashboard",
                      g_ShowDashboard, clrLime, clrGray, "SHOW_DASH");
    row++;

    CreateToggleButton("BTN_SHOW_COMM", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Commentary",
                      g_ShowCommentary, clrLime, clrGray, "SHOW_COMM");
    row++;

    CreateToggleButton("BTN_SHOW_LEGEND", x_start, y_start + row * (button_height + spacing),
                      button_width, button_height,
                      "Color Legend",
                      g_ShowColorLegend, clrLime, clrGray, "SHOW_LEGEND");
    row++;

    // Update all button displays
    UpdateAllButtons();
}

//+------------------------------------------------------------------+
//| CREATE TOGGLE BUTTON                                             |
//+------------------------------------------------------------------+
void CreateToggleButton(string name, int x, int y, int width, int height,
                       string text, bool initial_state,
                       color col_on, color col_off, string setting_name)
{
    if(button_count >= 50) return;  // Fixed limit

    // Store button data
    gui_buttons[button_count].name = prefix + name;
    gui_buttons[button_count].x = x;
    gui_buttons[button_count].y = y;
    gui_buttons[button_count].width = width;
    gui_buttons[button_count].height = height;
    gui_buttons[button_count].text = text;
    gui_buttons[button_count].state = initial_state;
    gui_buttons[button_count].color_on = col_on;
    gui_buttons[button_count].color_off = col_off;
    gui_buttons[button_count].setting = setting_name;

    // Create proper button object (OBJ_BUTTON has built-in text and click handling)
    ObjectCreate(0, gui_buttons[button_count].name, OBJ_BUTTON, 0, 0, 0);
    ObjectSetInteger(0, gui_buttons[button_count].name, OBJPROP_XDISTANCE, x);
    ObjectSetInteger(0, gui_buttons[button_count].name, OBJPROP_YDISTANCE, y);
    ObjectSetInteger(0, gui_buttons[button_count].name, OBJPROP_XSIZE, width);
    ObjectSetInteger(0, gui_buttons[button_count].name, OBJPROP_YSIZE, height);
    ObjectSetInteger(0, gui_buttons[button_count].name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
    ObjectSetInteger(0, gui_buttons[button_count].name, OBJPROP_BGCOLOR,
                    initial_state ? col_on : col_off);
    // Set text color: Black for green buttons (ON), White for grey/off buttons
    color text_color = (initial_state && col_on == clrLime) ? clrBlack : clrWhite;
    ObjectSetInteger(0, gui_buttons[button_count].name, OBJPROP_COLOR, text_color);
    ObjectSetInteger(0, gui_buttons[button_count].name, OBJPROP_BORDER_COLOR, clrWhite);
    ObjectSetString(0, gui_buttons[button_count].name, OBJPROP_FONT, "Arial Bold");
    ObjectSetInteger(0, gui_buttons[button_count].name, OBJPROP_FONTSIZE, 10);
    ObjectSetString(0, gui_buttons[button_count].name, OBJPROP_TEXT,
                   text + (initial_state ? " [ON]" : " [OFF]"));
    ObjectSetInteger(0, gui_buttons[button_count].name, OBJPROP_STATE, false);  // Not pressed
    ObjectSetInteger(0, gui_buttons[button_count].name, OBJPROP_SELECTABLE, false);  // Not moveable
    ObjectSetInteger(0, gui_buttons[button_count].name, OBJPROP_ZORDER, 10);  // On top

    button_count++;
}

//+------------------------------------------------------------------+
//| CREATE BIG LABEL                                                 |
//+------------------------------------------------------------------+
void CreateBigLabel(string name, int x, int y, string text,
                   color clr, int font_size, bool bold)
{
    string label_name = prefix + name;
    ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
    ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x);
    ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, y);
    ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
    ObjectSetString(0, label_name, OBJPROP_FONT, bold ? "Arial Bold" : "Arial");
    ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, font_size);
    ObjectSetString(0, label_name, OBJPROP_TEXT, text);
    ObjectSetInteger(0, label_name, OBJPROP_COLOR, clr);
}

//+------------------------------------------------------------------+
//| UPDATE ALL BUTTONS DISPLAY                                       |
//+------------------------------------------------------------------+
void UpdateAllButtons()
{
    for(int i = 0; i < button_count; i++)
    {
        // Update background color based on state
        color bg_color = gui_buttons[i].state ? gui_buttons[i].color_on : gui_buttons[i].color_off;
        ObjectSetInteger(0, gui_buttons[i].name, OBJPROP_BGCOLOR, bg_color);

        // Set text color: Black for green buttons (ON), White for grey/off buttons
        color text_color = (gui_buttons[i].state && gui_buttons[i].color_on == clrLime) ? clrBlack : clrWhite;
        ObjectSetInteger(0, gui_buttons[i].name, OBJPROP_COLOR, text_color);

        // Update button text with state indicator
        string button_text = gui_buttons[i].text + (gui_buttons[i].state ? " [ON]" : " [OFF]");
        ObjectSetString(0, gui_buttons[i].name, OBJPROP_TEXT, button_text);

        // Reset button pressed state
        ObjectSetInteger(0, gui_buttons[i].name, OBJPROP_STATE, false);
    }

    // Force chart redraw
    ChartRedraw();
}


//+------------------------------------------------------------------+
//| UPDATE ACTUAL SETTING VARIABLE                                   |
//| NOTE: Updates shadow global variables (g_*) not input parameters |
//+------------------------------------------------------------------+
void UpdateSetting(string setting, bool value)
{
    if(setting == "MINIMIZE")
    {
        // Special handling for minimize - toggle the GUI
        ToggleGuiMinimize();
    }
    else if(setting == "MODE")
    {
        g_EnableTrading = value;
        if(value)
            AddComment("⚠ AUTO-TRADING ENABLED - EA will execute trades!", clrRed, PRIORITY_CRITICAL);
        else
            AddComment("✓ Switched to INDICATOR MODE - No trading", clrLime, PRIORITY_CRITICAL);
    }
    else if(setting == "VOLUME") g_UseVolumeFilter = value;
    else if(setting == "SPREAD") g_UseSpreadFilter = value;
    else if(setting == "SLIPPAGE") g_UseSlippageModel = value;
    else if(setting == "MTF") g_UseMTFConfirmation = value;
    else if(setting == "SESSION") g_UseSessionFilter = value;
    else if(setting == "CORRELATION") g_UseCorrelationFilter = value;
    else if(setting == "NEWS") g_UseNewsFilter = value;
    else if(setting == "VOLATILITY") g_UseVolatilityAdaptation = value;
    else if(setting == "DYNAMIC_RISK") g_UseDynamicRisk = value;
    else if(setting == "PATTERN_DECAY") g_UsePatternDecay = value;
    else if(setting == "LIQUIDITY") g_UseLiquiditySweep = value;
    else if(setting == "RETAIL_TRAP") g_UseRetailTrap = value;
    else if(setting == "OB_INVALID") g_UseOrderBlockInvalidation = value;
    else if(setting == "STRUCTURE") g_UseMarketStructure = value;
    else if(setting == "ML_ENABLE")
    {
        g_MLEnabled = value;

        if(value)
        {
            // If ML is being enabled and ml_system doesn't exist, create and initialize it
            if(ml_system == NULL)
            {
                Print("\n╔═══════════════════════════════════════════════════════════╗");
                Print("║   ML SYSTEM ENABLED VIA GUI - INITIALIZING NOW           ║");
                Print("╚═══════════════════════════════════════════════════════════╝");

                ml_system = new CMLTradingSystem();

                MLConfig ml_config;
                ml_config.enabled = true;
                ml_config.use_for_filtering = ML_UseForFiltering;
                ml_config.use_for_sizing = ML_UseForSizing;
                ml_config.collect_training_data = ML_CollectData;
                ml_config.min_probability_threshold = ML_MinProbability;
                ml_config.min_confidence_threshold = ML_MinConfidence;
                ml_config.retrain_every_n_trades = ML_RetrainEvery;
                ml_config.auto_export_data = ML_AutoExport;

                if(ml_system.Initialize(ml_config))
                {
                    Print("✓ ML System initialized successfully via GUI button");
                    AddComment("✓ ML SYSTEM ENABLED - Machine Learning active", clrLime, PRIORITY_CRITICAL);
                    AddComment("🤖 ML System initialized and ready", clrLime, PRIORITY_IMPORTANT);
                }
                else
                {
                    Print("WARNING: ML System initialization failed");
                    AddComment("⚠ ML System init failed - check logs", clrOrange, PRIORITY_CRITICAL);
                    // Clean up the failed ml_system object
                    delete ml_system;
                    ml_system = NULL;
                    g_MLEnabled = false;  // Revert to disabled state
                }
            }
            else
            {
                AddComment("✓ ML SYSTEM ENABLED - Machine Learning active", clrLime, PRIORITY_CRITICAL);
            }
        }
        else
        {
            AddComment("⛔ ML SYSTEM DISABLED - Machine Learning inactive", clrOrange, PRIORITY_CRITICAL);
            // Note: We keep ml_system object alive but set g_MLEnabled = false
            // This allows re-enabling without losing trained data
        }

        // Update the ML Status panel immediately
        DrawMLStatus();
    }
    else if(setting == "PATTERN_TRACK") g_UsePatternTracking = value;
    else if(setting == "ADAPTATION") g_UseParameterAdaptation = value;
    else if(setting == "REGIME_STRATEGY") g_UseRegimeStrategy = value;
    // Visual toggles
    else if(setting == "SHOW_PATTERNS") g_ShowPatternBoxes = value;
    else if(setting == "SHOW_LABELS") g_ShowPatternLabels = value;
    else if(setting == "SHOW_LIQ") g_ShowLiquidityZones = value;
    else if(setting == "SHOW_FVG") g_ShowFVGZones = value;
    else if(setting == "SHOW_OB") g_ShowOrderBlocks = value;
    else if(setting == "SHOW_DASH") g_ShowDashboard = value;
    else if(setting == "SHOW_COMM") g_ShowCommentary = value;
    else if(setting == "SHOW_LEGEND") g_ShowColorLegend = value;
}

//+------------------------------------------------------------------+
//| DRAW REAL-TIME ANALYSIS PANEL (Structured Display)               |
//+------------------------------------------------------------------+
void DrawBigCommentary()
{
    string box_name = prefix + "Commentary_Box";

    if(!g_ShowCommentary)
    {
        // Hide analysis panel
        ObjectDelete(0, box_name);
        for(int i = 0; i < 50; i++)
        {
            ObjectDelete(0, prefix + "RTA_" + IntegerToString(i));
        }
        return;
    }

    int x = 750;   // Right side
    int y = 50;    // Top of chart
    int width = 550;
    int line_height = 22;

    // Background box - BIGGER to show all structured info
    if(ObjectFind(0, box_name) < 0)
    {
        ObjectCreate(0, box_name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
        ObjectSetInteger(0, box_name, OBJPROP_XDISTANCE, x);
        ObjectSetInteger(0, box_name, OBJPROP_YDISTANCE, y);
        ObjectSetInteger(0, box_name, OBJPROP_XSIZE, width);
        ObjectSetInteger(0, box_name, OBJPROP_YSIZE, 400);  // Tall enough for all info
        ObjectSetInteger(0, box_name, OBJPROP_BGCOLOR, C'20,25,35');
        ObjectSetInteger(0, box_name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0, box_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetInteger(0, box_name, OBJPROP_BACK, true);
    }

    // Title
    string title_name = prefix + "Commentary_Title";
    if(ObjectFind(0, title_name) < 0)
    {
        ObjectCreate(0, title_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, title_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, title_name, OBJPROP_FONT, "Arial Bold");
        ObjectSetInteger(0, title_name, OBJPROP_FONTSIZE, 13);
    }
    ObjectSetInteger(0, title_name, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, title_name, OBJPROP_YDISTANCE, y + 8);
    ObjectSetString(0, title_name, OBJPROP_TEXT, "═══ REAL-TIME ANALYSIS ═══");
    ObjectSetInteger(0, title_name, OBJPROP_COLOR, clrYellow);

    int row = 0;
    int base_y = y + 35;

    // Order Blocks Info
    int active_ob = 0;
    for(int i = 0; i < ob_count; i++)
        if(!order_blocks[i].invalidated) active_ob++;

    string label_name = prefix + "RTA_" + IntegerToString(row);
    if(ObjectFind(0, label_name) < 0)
    {
        ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");
        ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 11);
    }
    ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, base_y + row * line_height);
    ObjectSetString(0, label_name, OBJPROP_TEXT, "Order Blocks: " + IntegerToString(active_ob) + " active");
    ObjectSetInteger(0, label_name, OBJPROP_COLOR, clrAqua);
    row++;
    row++; // Extra spacing

    // Phase 3: Pattern Detection Header
    label_name = prefix + "RTA_" + IntegerToString(row);
    if(ObjectFind(0, label_name) < 0)
    {
        ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");
        ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 11);
    }
    ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, base_y + row * line_height);
    ObjectSetString(0, label_name, OBJPROP_TEXT, "─── Phase 3: Pattern Detection ───");
    ObjectSetInteger(0, label_name, OBJPROP_COLOR, clrCyan);
    row++;

    // H4 Pattern (Main Timeframe)
    label_name = prefix + "RTA_" + IntegerToString(row);
    if(ObjectFind(0, label_name) < 0)
    {
        ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");
        ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 11);
    }
    ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, base_y + row * line_height);
    if(has_active_pattern)
    {
        string h4_arrow = active_pattern.is_bullish ? "↑" : "↓";
        ObjectSetString(0, label_name, OBJPROP_TEXT,
                       "H4: " + active_pattern.name + " " + h4_arrow + " [" +
                       IntegerToString(active_pattern.strength) + "★]");
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, active_pattern.is_bullish ? clrLime : clrRed);
    }
    else
    {
        ObjectSetString(0, label_name, OBJPROP_TEXT, "H4: No pattern detected");
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, clrGray);
    }
    row++;

    // H1 Pattern
    label_name = prefix + "RTA_" + IntegerToString(row);
    if(ObjectFind(0, label_name) < 0)
    {
        ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");
        ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 11);
    }
    ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, base_y + row * line_height);
    if(has_active_pattern_h1)
    {
        string h1_arrow = active_pattern_h1.is_bullish ? "↑" : "↓";
        ObjectSetString(0, label_name, OBJPROP_TEXT,
                       "H1: " + active_pattern_h1.name + " " + h1_arrow + " [" +
                       IntegerToString(active_pattern_h1.strength) + "★]");
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, active_pattern_h1.is_bullish ? clrLime : clrRed);
    }
    else
    {
        ObjectSetString(0, label_name, OBJPROP_TEXT, "H1: No pattern detected");
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, clrGray);
    }
    row++;

    // M15 Pattern
    label_name = prefix + "RTA_" + IntegerToString(row);
    if(ObjectFind(0, label_name) < 0)
    {
        ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");
        ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 11);
    }
    ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, base_y + row * line_height);
    if(has_active_pattern_m15)
    {
        string m15_arrow = active_pattern_m15.is_bullish ? "↑" : "↓";
        ObjectSetString(0, label_name, OBJPROP_TEXT,
                       "M15: " + active_pattern_m15.name + " " + m15_arrow + " [" +
                       IntegerToString(active_pattern_m15.strength) + "★]");
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, active_pattern_m15.is_bullish ? clrLime : clrRed);
    }
    else
    {
        ObjectSetString(0, label_name, OBJPROP_TEXT, "M15: No pattern detected");
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, clrGray);
    }
    row++;
    row++; // Spacing

    // Confluence Score (if pattern exists)
    if(has_active_pattern)
    {
        label_name = prefix + "RTA_" + IntegerToString(row);
        if(ObjectFind(0, label_name) < 0)
        {
            ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
            ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
            ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");
            ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 11);
        }
        ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10);
        ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, base_y + row * line_height);
        ObjectSetString(0, label_name, OBJPROP_TEXT,
                       "Confluence: " + IntegerToString(last_decision.confluence_score) +
                       "/" + IntegerToString(dynamic_confluence_required));
        ObjectSetInteger(0, label_name, OBJPROP_COLOR,
                        last_decision.confluence_score >= dynamic_confluence_required ? clrLime : clrOrange);
        row++;
        row++; // Spacing

        // Decision
        label_name = prefix + "RTA_" + IntegerToString(row);
        if(ObjectFind(0, label_name) < 0)
        {
            ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
            ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
            ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");
            ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 11);
        }
        ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10);
        ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, base_y + row * line_height);

        string decision_text = "";
        color decision_color = clrWhite;
        switch(last_decision.decision)
        {
            case DECISION_ENTER:
                decision_text = "✓ DECISION: ENTER TRADE";
                decision_color = clrLime;
                break;
            case DECISION_SKIP:
                decision_text = "⛔ DECISION: SKIP TRADE";
                decision_color = clrRed;
                break;
            case DECISION_WAIT:
                decision_text = "⏸ DECISION: WAIT";
                decision_color = clrYellow;
                break;
        }
        ObjectSetString(0, label_name, OBJPROP_TEXT, decision_text);
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, decision_color);
        row++;

        // Signal Timestamp - Show when pattern was detected
        label_name = prefix + "RTA_" + IntegerToString(row);
        if(ObjectFind(0, label_name) < 0)
        {
            ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
            ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
            ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");
            ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 10);
        }
        ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10);
        ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, base_y + row * line_height);
        ObjectSetString(0, label_name, OBJPROP_TEXT,
                       "Signal Generated: " + TimeToString(active_pattern.detected_time, TIME_DATE|TIME_MINUTES));
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, clrCyan);
        row++;

        // Show when the signal was detected using DD.MM.YY.HH:MM format
        string signal_time = FormatTimeDifference(active_pattern.detected_time);

        label_name = prefix + "RTA_" + IntegerToString(row);
        if(ObjectFind(0, label_name) < 0)
        {
            ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
            ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
            ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");
            ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 10);
        }
        ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10);
        ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, base_y + row * line_height);
        ObjectSetString(0, label_name, OBJPROP_TEXT, "Detected At: [" + signal_time + "]");
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, clrGray);
        row++;
    }
    else
    {
        label_name = prefix + "RTA_" + IntegerToString(row);
        if(ObjectFind(0, label_name) < 0)
        {
            ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
            ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
            ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");
            ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 10);
        }
        ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10);
        ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, base_y + row * line_height);
        ObjectSetString(0, label_name, OBJPROP_TEXT, "No valid patterns detected - Waiting...");
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, clrGray);
        row++;
    }

    row++; // Spacing

    // Current Advice - Show last commentary line with "ADVICE:"
    string advice_text = "";
    color advice_color = clrYellow;
    for(int i = commentary_count - 1; i >= 0; i--)
    {
        if(StringFind(commentary_buffer[i].text, "ADVICE:") >= 0)
        {
            advice_text = commentary_buffer[i].text;
            advice_color = commentary_buffer[i].text_color;
            break;
        }
    }
    if(advice_text == "")
        advice_text = "ADVICE: Patience is key - Wait for high-quality setups";

    label_name = prefix + "RTA_" + IntegerToString(row);
    if(ObjectFind(0, label_name) < 0)
    {
        ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");
        ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 10);
    }
    ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, base_y + row * line_height);
    ObjectSetString(0, label_name, OBJPROP_TEXT, advice_text);
    ObjectSetInteger(0, label_name, OBJPROP_COLOR, advice_color);
}

//+------------------------------------------------------------------+
//| DRAW COLOR LEGEND - Explains what each color means               |
//+------------------------------------------------------------------+
void DrawColorLegend()
{
    string legend_name = prefix + "Legend_BG";

    if(!g_ShowColorLegend)
    {
        // Hide legend
        ObjectDelete(0, legend_name);
        for(int i = 0; i < 20; i++)
        {
            ObjectDelete(0, prefix + "Legend_" + IntegerToString(i));
            ObjectDelete(0, prefix + "LegendBox_" + IntegerToString(i));
        }
        return;
    }

    int x = 20;
    int y = 10;   // Distance from bottom (using CORNER_LEFT_LOWER)
    int width = 280;
    int line_height = 22;

    // Build from bottom up - higher row numbers = higher on screen
    int base_y = y + 10;

    // Order Blocks (bottom of legend)
    int row = 1;
    CreateColorBox(8, x+10, base_y + row*line_height, clrCrimson);
    CreateLegendLabel(8, x+35, base_y + row*line_height, "Bearish Order Block", clrWhite, 10, false);
    row++;

    CreateColorBox(7, x+10, base_y + row*line_height, C'0,100,0');
    CreateLegendLabel(7, x+35, base_y + row*line_height, "Bullish Order Block", clrWhite, 10, false);
    row++;

    row++;  // Spacing

    // Fair Value Gaps
    CreateColorBox(6, x+10, base_y + row*line_height, clrLightPink);
    CreateLegendLabel(6, x+35, base_y + row*line_height, "Bearish FVG (Gap Down)", clrWhite, 10, false);
    row++;

    CreateColorBox(5, x+10, base_y + row*line_height, clrLightGreen);
    CreateLegendLabel(5, x+35, base_y + row*line_height, "Bullish FVG (Gap Up)", clrWhite, 10, false);
    row++;

    row++;  // Spacing

    // Liquidity zones
    CreateColorBox(4, x+10, base_y + row*line_height, clrBlue);
    CreateLegendLabel(4, x+35, base_y + row*line_height, "Liquidity Low (Buy Side)", clrWhite, 10, false);
    row++;

    CreateColorBox(3, x+10, base_y + row*line_height, clrRed);
    CreateLegendLabel(3, x+35, base_y + row*line_height, "Liquidity High (Sell Side)", clrWhite, 10, false);
    row++;

    row++;  // Spacing

    // Pattern colors
    CreateColorBox(2, x+10, base_y + row*line_height, clrRed);
    CreateLegendLabel(2, x+35, base_y + row*line_height, "Bearish Pattern", clrWhite, 10, false);
    row++;

    CreateColorBox(1, x+10, base_y + row*line_height, clrLime);
    CreateLegendLabel(1, x+35, base_y + row*line_height, "Bullish Pattern", clrWhite, 10, false);
    row++;

    // Title (at top)
    CreateLegendLabel(0, x+10, base_y + row*line_height + 8, "═══ COLOR LEGEND ═══", clrWhite, 11, true);
    row++;

    // Calculate proper background height based on content
    int total_height = base_y + row*line_height + 15;  // +15 for top padding

    // Background box - BLACK BACKGROUND with proper size
    if(ObjectFind(0, legend_name) < 0)
    {
        ObjectCreate(0, legend_name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
        ObjectSetInteger(0, legend_name, OBJPROP_CORNER, CORNER_LEFT_LOWER);
        ObjectSetInteger(0, legend_name, OBJPROP_BACK, false);
        ObjectSetInteger(0, legend_name, OBJPROP_BGCOLOR, clrBlack);  // Pure black background
        ObjectSetInteger(0, legend_name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0, legend_name, OBJPROP_COLOR, clrWhite);  // White border
    }

    // Update background position and size
    ObjectSetInteger(0, legend_name, OBJPROP_XDISTANCE, x);
    ObjectSetInteger(0, legend_name, OBJPROP_YDISTANCE, y);
    ObjectSetInteger(0, legend_name, OBJPROP_XSIZE, width);
    ObjectSetInteger(0, legend_name, OBJPROP_YSIZE, total_height);
}

//+------------------------------------------------------------------+
//| CREATE COLOR BOX (Small colored square for legend)               |
//+------------------------------------------------------------------+
void CreateColorBox(int index, int x, int y, color clr)
{
    string name = prefix + "LegendBox_" + IntegerToString(index);

    if(ObjectFind(0, name) < 0)
    {
        ObjectCreate(0, name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
        ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_LOWER);
        ObjectSetInteger(0, name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0, name, OBJPROP_COLOR, clrWhite);  // White border for better visibility
        ObjectSetInteger(0, name, OBJPROP_BACK, false);
    }

    // Align box vertically centered with text (text is at y, box needs offset to center)
    ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
    ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);  // Same Y as text for proper alignment
    ObjectSetInteger(0, name, OBJPROP_XSIZE, 18);
    ObjectSetInteger(0, name, OBJPROP_YSIZE, 18);
    ObjectSetInteger(0, name, OBJPROP_BGCOLOR, clr);
}

//+------------------------------------------------------------------+
//| CREATE LEGEND LABEL                                              |
//+------------------------------------------------------------------+
void CreateLegendLabel(int index, int x, int y, string text, color clr, int font_size, bool bold)
{
    string name = prefix + "Legend_" + IntegerToString(index);

    if(ObjectFind(0, name) < 0)
    {
        ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_LOWER);
        ObjectSetInteger(0, name, OBJPROP_ANCHOR, ANCHOR_LEFT);  // Use left anchor for better alignment
        ObjectSetString(0, name, OBJPROP_FONT, bold ? "Arial Bold" : "Arial");
        ObjectSetInteger(0, name, OBJPROP_FONTSIZE, font_size);
    }

    // Position text at same Y as color box for perfect alignment
    ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
    ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y + 9);  // +9 to vertically center text with 18px box
    ObjectSetString(0, name, OBJPROP_TEXT, text);
    ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
}

//+------------------------------------------------------------------+
//| DRAW BUTTON STATUS (Near MARKET STATUS as requested)             |
//+------------------------------------------------------------------+
void DrawButtonStatus()
{
    string box_name = prefix + "ButtonStatus_Box";

    // Button status displayed BELOW at MARKET STATUS level as user requested
    int x = 320;   // Aligned with commentary
    int y = 160;   // MOVED DOWN - below Real-Time Analysis, above chart main area
    int width = 800;
    int line_height = 22;  // Compact spacing
    int max_lines = 3;     // Only show last 3 button changes to keep it compact

    // Background box - Compact and clean
    if(ObjectFind(0, box_name) < 0)
    {
        ObjectCreate(0, box_name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
        ObjectSetInteger(0, box_name, OBJPROP_XDISTANCE, x);
        ObjectSetInteger(0, box_name, OBJPROP_YDISTANCE, y);
        ObjectSetInteger(0, box_name, OBJPROP_XSIZE, width);
        ObjectSetInteger(0, box_name, OBJPROP_YSIZE, 35 + max_lines * line_height);
        ObjectSetInteger(0, box_name, OBJPROP_BGCOLOR, C'15,15,25');  // Darker to distinguish from commentary
        ObjectSetInteger(0, box_name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0, box_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetInteger(0, box_name, OBJPROP_BACK, true);
    }

    // Title
    string title_name = prefix + "ButtonStatus_Title";
    if(ObjectFind(0, title_name) < 0)
    {
        ObjectCreate(0, title_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, title_name, OBJPROP_XDISTANCE, x + 10);
        ObjectSetInteger(0, title_name, OBJPROP_YDISTANCE, y + 6);
        ObjectSetInteger(0, title_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, title_name, OBJPROP_FONT, "Arial Bold");
        ObjectSetInteger(0, title_name, OBJPROP_FONTSIZE, 11);
        ObjectSetString(0, title_name, OBJPROP_TEXT, "══ BUTTON STATUS ══");
        ObjectSetInteger(0, title_name, OBJPROP_COLOR, clrCyan);
    }

    // Clear old button status labels
    for(int i = 0; i < 10; i++)
    {
        string label_name = prefix + "ButtonStatus_" + IntegerToString(i);
        ObjectDelete(0, label_name);
    }

    // Draw button status lines - show last few button changes
    int start_index = MathMax(0, button_status_count - max_lines);

    for(int i = start_index; i < button_status_count; i++)
    {
        string label_name = prefix + "ButtonStatus_" + IntegerToString(i);

        ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetInteger(0, label_name, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");
        ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 10);

        ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10);
        ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, y + 28 + (i - start_index) * line_height);
        ObjectSetString(0, label_name, OBJPROP_TEXT, button_status_buffer[i].text);
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, button_status_buffer[i].text_color);
    }

    // Show message if no button changes yet
    if(button_status_count == 0)
    {
        string label_name = prefix + "ButtonStatus_0";
        ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");
        ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 10);
        ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10);
        ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, y + 28);
        ObjectSetString(0, label_name, OBJPROP_TEXT, "Ready - Click buttons to configure filters...");
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, clrGray);
    }
}

//+------------------------------------------------------------------+
//| DRAW ML STATUS & COMMENTARY - Real-time ML System Monitor        |
//+------------------------------------------------------------------+
void DrawMLStatus()
{
    string box_name = prefix + "MLStatus_Box";

    // Position: Below Button Status, compact design
    int x = 320;
    int y = 280;   // Below Button Status
    int width = 800;
    int line_height = 20;

    // Check if ML is enabled
    if(ml_system == NULL || !g_MLEnabled)
    {
        // Show "ML SYSTEM DISABLED" message
        if(ObjectFind(0, box_name) < 0)
        {
            ObjectCreate(0, box_name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
            ObjectSetInteger(0, box_name, OBJPROP_XDISTANCE, x);
            ObjectSetInteger(0, box_name, OBJPROP_YDISTANCE, y);
            ObjectSetInteger(0, box_name, OBJPROP_XSIZE, width);
            ObjectSetInteger(0, box_name, OBJPROP_YSIZE, 60);
            ObjectSetInteger(0, box_name, OBJPROP_BGCOLOR, C'25,15,15');  // Reddish tint
            ObjectSetInteger(0, box_name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
            ObjectSetInteger(0, box_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
            ObjectSetInteger(0, box_name, OBJPROP_BACK, true);
        }

        string title_name = prefix + "MLStatus_Title";
        if(ObjectFind(0, title_name) < 0)
        {
            ObjectCreate(0, title_name, OBJ_LABEL, 0, 0, 0);
            ObjectSetInteger(0, title_name, OBJPROP_XDISTANCE, x + 10);
            ObjectSetInteger(0, title_name, OBJPROP_YDISTANCE, y + 6);
            ObjectSetInteger(0, title_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
            ObjectSetString(0, title_name, OBJPROP_FONT, "Arial Bold");
            ObjectSetInteger(0, title_name, OBJPROP_FONTSIZE, 11);
            ObjectSetString(0, title_name, OBJPROP_TEXT, "══ 🤖 ML SYSTEM STATUS ══");
            ObjectSetInteger(0, title_name, OBJPROP_COLOR, clrOrangeRed);
        }

        string status_name = prefix + "MLStatus_Disabled";
        if(ObjectFind(0, status_name) < 0)
        {
            ObjectCreate(0, status_name, OBJ_LABEL, 0, 0, 0);
            ObjectSetInteger(0, status_name, OBJPROP_XDISTANCE, x + 10);
            ObjectSetInteger(0, status_name, OBJPROP_YDISTANCE, y + 30);
            ObjectSetInteger(0, status_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
            ObjectSetString(0, status_name, OBJPROP_FONT, "Arial");
            ObjectSetInteger(0, status_name, OBJPROP_FONTSIZE, 10);
            ObjectSetString(0, status_name, OBJPROP_TEXT, "⛔ ML SYSTEM DISABLED - Set ML_Enabled=true to activate data collection and filtering");
            ObjectSetInteger(0, status_name, OBJPROP_COLOR, clrGray);
        }

        return;
    }

    // ML IS ENABLED - Show full status panel
    int sample_count = ml_system.GetSampleCount();
    bool is_collecting = (sample_count < 50);
    int panel_height = 155 + (ml_action_count * line_height);  // Dynamic height based on actions

    // Background box
    if(ObjectFind(0, box_name) < 0)
    {
        ObjectCreate(0, box_name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
        ObjectSetInteger(0, box_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetInteger(0, box_name, OBJPROP_BACK, true);
        ObjectSetInteger(0, box_name, OBJPROP_BGCOLOR, C'15,25,20');  // Greenish tint for active
        ObjectSetInteger(0, box_name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
    }
    ObjectSetInteger(0, box_name, OBJPROP_XDISTANCE, x);
    ObjectSetInteger(0, box_name, OBJPROP_YDISTANCE, y);
    ObjectSetInteger(0, box_name, OBJPROP_XSIZE, width);
    ObjectSetInteger(0, box_name, OBJPROP_YSIZE, panel_height);

    // Title
    string title_name = prefix + "MLStatus_Title";
    if(ObjectFind(0, title_name) < 0)
    {
        ObjectCreate(0, title_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, title_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, title_name, OBJPROP_FONT, "Arial Bold");
        ObjectSetInteger(0, title_name, OBJPROP_FONTSIZE, 11);
    }
    ObjectSetInteger(0, title_name, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, title_name, OBJPROP_YDISTANCE, y + 6);
    ObjectSetString(0, title_name, OBJPROP_TEXT, "══ 🤖 ML SYSTEM STATUS & COMMENTARY ══");
    ObjectSetInteger(0, title_name, OBJPROP_COLOR, clrLime);

    int current_y = y + 30;

    // LINE 1: System State
    string state_name = prefix + "MLStatus_State";
    string state_text = "";
    color state_color = clrWhite;

    if(is_collecting)
    {
        state_text = "🔄 MODE: DATA COLLECTION (" + IntegerToString(sample_count) + "/50 samples) - All trades approved, learning in progress";
        state_color = clrYellow;
    }
    else
    {
        state_text = "✅ MODE: ACTIVE FILTERING - ML is evaluating and filtering trades";
        state_color = clrLime;
    }

    if(ObjectFind(0, state_name) < 0)
    {
        ObjectCreate(0, state_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, state_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, state_name, OBJPROP_FONT, "Arial Bold");
        ObjectSetInteger(0, state_name, OBJPROP_FONTSIZE, 10);
    }
    ObjectSetInteger(0, state_name, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, state_name, OBJPROP_YDISTANCE, current_y);
    ObjectSetString(0, state_name, OBJPROP_TEXT, state_text);
    ObjectSetInteger(0, state_name, OBJPROP_COLOR, state_color);
    current_y += line_height;

    // LINE 2: Progress Bar (visual representation)
    string progress_name = prefix + "MLStatus_Progress";
    double progress_percent = (sample_count / 50.0) * 100.0;
    if(progress_percent > 100) progress_percent = 100;

    string progress_bar = "📊 TRAINING DATA: [";
    int bar_length = 30;
    int filled = (int)((progress_percent / 100.0) * bar_length);
    for(int i = 0; i < bar_length; i++)
        progress_bar += (i < filled) ? "█" : "░";
    progress_bar += "] " + IntegerToString(sample_count) + " samples | " + DoubleToString(progress_percent, 1) + "%";

    if(ObjectFind(0, progress_name) < 0)
    {
        ObjectCreate(0, progress_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, progress_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, progress_name, OBJPROP_FONT, "Courier New");
        ObjectSetInteger(0, progress_name, OBJPROP_FONTSIZE, 9);
    }
    ObjectSetInteger(0, progress_name, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, progress_name, OBJPROP_YDISTANCE, current_y);
    ObjectSetString(0, progress_name, OBJPROP_TEXT, progress_bar);
    ObjectSetInteger(0, progress_name, OBJPROP_COLOR, clrAqua);
    current_y += line_height;

    // LINE 3: Model Performance Metrics
    string metrics_name = prefix + "MLStatus_Metrics";
    string metrics_text = "";

    if(is_collecting)
    {
        int remaining = 50 - sample_count;
        metrics_text = "⏳ STATUS: Collecting data from live trades | " + IntegerToString(remaining) + " more samples needed before ML filtering activates";
    }
    else
    {
        // Show filtering thresholds
        metrics_text = StringFormat("🎯 FILTERING: Min Probability %.0f%% | Min Confidence %.0f%% | Retraining every %d trades",
                                   ML_MinProbability * 100, ML_MinConfidence * 100, ML_RetrainEvery);
    }

    if(ObjectFind(0, metrics_name) < 0)
    {
        ObjectCreate(0, metrics_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, metrics_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, metrics_name, OBJPROP_FONT, "Arial");
        ObjectSetInteger(0, metrics_name, OBJPROP_FONTSIZE, 9);
    }
    ObjectSetInteger(0, metrics_name, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, metrics_name, OBJPROP_YDISTANCE, current_y);
    ObjectSetString(0, metrics_name, OBJPROP_TEXT, metrics_text);
    ObjectSetInteger(0, metrics_name, OBJPROP_COLOR, clrSilver);
    current_y += line_height + 5;

    // Separator
    string sep1_name = prefix + "MLStatus_Sep1";
    if(ObjectFind(0, sep1_name) < 0)
    {
        ObjectCreate(0, sep1_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, sep1_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, sep1_name, OBJPROP_FONT, "Arial");
        ObjectSetInteger(0, sep1_name, OBJPROP_FONTSIZE, 9);
    }
    ObjectSetInteger(0, sep1_name, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, sep1_name, OBJPROP_YDISTANCE, current_y);
    ObjectSetString(0, sep1_name, OBJPROP_TEXT, "─── RECENT ML ACTIONS ───");
    ObjectSetInteger(0, sep1_name, OBJPROP_COLOR, clrGray);
    current_y += line_height;

    // Recent ML Actions (last 5 actions)
    if(ml_action_count == 0)
    {
        string no_action_name = prefix + "MLStatus_NoActions";
        if(ObjectFind(0, no_action_name) < 0)
        {
            ObjectCreate(0, no_action_name, OBJ_LABEL, 0, 0, 0);
            ObjectSetInteger(0, no_action_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
            ObjectSetString(0, no_action_name, OBJPROP_FONT, "Arial");
            ObjectSetInteger(0, no_action_name, OBJPROP_FONTSIZE, 9);
        }
        ObjectSetInteger(0, no_action_name, OBJPROP_XDISTANCE, x + 10);
        ObjectSetInteger(0, no_action_name, OBJPROP_YDISTANCE, current_y);
        ObjectSetString(0, no_action_name, OBJPROP_TEXT, "Waiting for trading signals to evaluate...");
        ObjectSetInteger(0, no_action_name, OBJPROP_COLOR, clrGray);
    }
    else
    {
        // Show last 5 actions
        int max_actions = 5;
        int start_index = MathMax(0, ml_action_count - max_actions);

        for(int i = start_index; i < ml_action_count; i++)
        {
            string action_name = prefix + "MLStatus_Action_" + IntegerToString(i);

            if(ObjectFind(0, action_name) < 0)
            {
                ObjectCreate(0, action_name, OBJ_LABEL, 0, 0, 0);
                ObjectSetInteger(0, action_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
                ObjectSetString(0, action_name, OBJPROP_FONT, "Arial");
                ObjectSetInteger(0, action_name, OBJPROP_FONTSIZE, 9);
            }

            ObjectSetInteger(0, action_name, OBJPROP_XDISTANCE, x + 20);
            ObjectSetInteger(0, action_name, OBJPROP_YDISTANCE, current_y);

            string time_str = TimeToString(ml_action_buffer[i].timestamp, TIME_MINUTES);
            string action_display = "[" + time_str + "] " + ml_action_buffer[i].action_text;

            ObjectSetString(0, action_name, OBJPROP_TEXT, action_display);
            ObjectSetInteger(0, action_name, OBJPROP_COLOR, ml_action_buffer[i].text_color);

            current_y += line_height;
        }
    }
}

//+------------------------------------------------------------------+
//| ADD ML ACTION TO BUFFER (Called from ML system)                  |
//+------------------------------------------------------------------+
void AddMLAction(string action_text, color text_color, bool was_approved)
{
    if(ml_action_count >= 20)
    {
        // Shift buffer
        for(int i = 0; i < 19; i++)
            ml_action_buffer[i] = ml_action_buffer[i + 1];
        ml_action_count = 19;
    }

    ml_action_buffer[ml_action_count].timestamp = TimeCurrent();
    ml_action_buffer[ml_action_count].action_text = action_text;
    ml_action_buffer[ml_action_count].text_color = text_color;
    ml_action_buffer[ml_action_count].was_approved = was_approved;
    ml_action_count++;

    // Redraw ML status panel
    DrawMLStatus();
}

//+------------------------------------------------------------------+
//| WRAP TEXT - Split long text into multiple lines                 |
//+------------------------------------------------------------------+
void WrapText(string text, string &lines[], int max_chars_per_line = 120)
{
    ArrayResize(lines, 0);

    // If text is shorter than max, return as single line
    if(StringLen(text) <= max_chars_per_line)
    {
        ArrayResize(lines, 1);
        lines[0] = text;
        return;
    }

    // Split long text into multiple lines
    int text_len = StringLen(text);
    int start = 0;

    while(start < text_len)
    {
        int line_len = MathMin(max_chars_per_line, text_len - start);

        // If not at the end, try to break at a space to avoid splitting words
        if(start + line_len < text_len)
        {
            // Look for last space within the line
            int last_space = -1;
            for(int i = start + line_len; i >= start && i > start + line_len - 20; i--)
            {
                if(StringGetCharacter(text, i) == ' ')
                {
                    last_space = i;
                    break;
                }
            }

            // If we found a space, break there
            if(last_space > start)
            {
                line_len = last_space - start;
            }
        }

        // Extract the line
        string line = StringSubstr(text, start, line_len);

        // Add to array
        int current_size = ArraySize(lines);
        ArrayResize(lines, current_size + 1);
        lines[current_size] = line;

        // Move to next line (skip the space if we broke at a space)
        start += line_len;
        if(start < text_len && StringGetCharacter(text, start) == ' ')
            start++;
    }
}

//+------------------------------------------------------------------+
//| DRAW PRICE ACTION COMMENTARY - Educational Deep Analysis         |
//+------------------------------------------------------------------+
void DrawPriceActionCommentary()
{
    string box_name = prefix + "PriceAction_Box";

    if(!g_ShowCommentary)
    {
        // Hide price action commentary
        ObjectDelete(0, box_name);
        ObjectDelete(0, prefix + "PriceAction_Title");
        ObjectDelete(0, prefix + "PAC_ServerTime");
        ObjectDelete(0, prefix + "PAC_LocalTime");
        for(int i = 0; i < 52; i++)  // 50 messages + 2 time headers
        {
            ObjectDelete(0, prefix + "PAC_" + IntegerToString(i));
        }
        return;
    }

    int x = 750;   // Right side, below Real-Time Analysis
    int y = 465;   // Below Real-Time Analysis panel
    int width = 5000;  // Massive panel to accommodate 2000+ character texts without any truncation
    int line_height = 20;
    int max_lines = 100;  // Show up to 100 messages with wrapped lines

    // Background box - SCROLLABLE COMMENTARY
    if(ObjectFind(0, box_name) < 0)
    {
        ObjectCreate(0, box_name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
        ObjectSetInteger(0, box_name, OBJPROP_XDISTANCE, x);
        ObjectSetInteger(0, box_name, OBJPROP_YDISTANCE, y);
        ObjectSetInteger(0, box_name, OBJPROP_XSIZE, width);
        ObjectSetInteger(0, box_name, OBJPROP_YSIZE, 800);  // Extra tall panel for massive texts
        ObjectSetInteger(0, box_name, OBJPROP_BGCOLOR, C'10,15,25');  // Dark blue background
        ObjectSetInteger(0, box_name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0, box_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetInteger(0, box_name, OBJPROP_BACK, true);
    }

    // Update width every frame to ensure changes take effect (for existing boxes)
    ObjectSetInteger(0, box_name, OBJPROP_XSIZE, width);

    // Title
    string title_name = prefix + "PriceAction_Title";
    if(ObjectFind(0, title_name) < 0)
    {
        ObjectCreate(0, title_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, title_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, title_name, OBJPROP_FONT, "Arial Bold");
        ObjectSetInteger(0, title_name, OBJPROP_FONTSIZE, 13);
    }
    ObjectSetInteger(0, title_name, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, title_name, OBJPROP_YDISTANCE, y + 8);
    ObjectSetString(0, title_name, OBJPROP_TEXT, "═══ PRICE ACTION COMMENTARY ═══");
    ObjectSetInteger(0, title_name, OBJPROP_COLOR, clrGold);

    // Server Time Header (Persistent)
    string server_time_label = prefix + "PAC_ServerTime";
    if(ObjectFind(0, server_time_label) < 0)
    {
        ObjectCreate(0, server_time_label, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, server_time_label, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, server_time_label, OBJPROP_FONT, "Arial Bold");
        ObjectSetInteger(0, server_time_label, OBJPROP_FONTSIZE, 10);
    }
    MqlDateTime dt_server;
    TimeToStruct(TimeCurrent(), dt_server);
    string server_time_text = StringFormat("Server Time: %02d.%02d.%02d.%02d:%02d",
                                           dt_server.day, dt_server.mon, dt_server.year % 100,
                                           dt_server.hour, dt_server.min);
    ObjectSetInteger(0, server_time_label, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, server_time_label, OBJPROP_YDISTANCE, y + 30);
    ObjectSetString(0, server_time_label, OBJPROP_TEXT, server_time_text);
    ObjectSetInteger(0, server_time_label, OBJPROP_COLOR, clrAqua);

    // Local Computer Time Header (Persistent)
    string local_time_label = prefix + "PAC_LocalTime";
    if(ObjectFind(0, local_time_label) < 0)
    {
        ObjectCreate(0, local_time_label, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, local_time_label, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, local_time_label, OBJPROP_FONT, "Arial Bold");
        ObjectSetInteger(0, local_time_label, OBJPROP_FONTSIZE, 10);
    }
    MqlDateTime dt_local;
    TimeToStruct(TimeLocal(), dt_local);
    string local_time_text = StringFormat("Local Time:  %02d.%02d.%02d.%02d:%02d",
                                          dt_local.day, dt_local.mon, dt_local.year % 100,
                                          dt_local.hour, dt_local.min);
    ObjectSetInteger(0, local_time_label, OBJPROP_XDISTANCE, x + 10);
    ObjectSetInteger(0, local_time_label, OBJPROP_YDISTANCE, y + 50);
    ObjectSetString(0, local_time_label, OBJPROP_TEXT, local_time_text);
    ObjectSetInteger(0, local_time_label, OBJPROP_COLOR, clrLightGreen);

    // Clear old commentary labels (increased to 500 to handle massive wrapped texts)
    for(int i = 0; i < 500; i++)
    {
        string label_name = prefix + "PAC_" + IntegerToString(i);
        ObjectDelete(0, label_name);
    }

    // Draw commentary lines (newest on top, oldest on bottom)
    int start_index = MathMax(0, pa_commentary_count - max_lines);
    int num_displayed = pa_commentary_count - start_index;

    // Show placeholder message if no commentary entries exist yet
    if(pa_commentary_count == 0)
    {
        string placeholder_name = prefix + "PAC_Placeholder";
        ObjectCreate(0, placeholder_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, placeholder_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetInteger(0, placeholder_name, OBJPROP_XDISTANCE, x + 10);
        ObjectSetInteger(0, placeholder_name, OBJPROP_YDISTANCE, y + 80);
        ObjectSetString(0, placeholder_name, OBJPROP_TEXT, "⏳ Awaiting market tick for Price Action analysis...");
        ObjectSetInteger(0, placeholder_name, OBJPROP_COLOR, clrGray);
        ObjectSetString(0, placeholder_name, OBJPROP_FONT, "Arial");
        ObjectSetInteger(0, placeholder_name, OBJPROP_FONTSIZE, 10);
        return;  // Exit early since there's nothing to display
    }
    else
    {
        // Remove placeholder if it exists
        ObjectDelete(0, prefix + "PAC_Placeholder");
    }

    // Loop BACKWARD through array to show NEWEST messages on TOP
    int display_line = 0;

    // DEBUG LOGGING
    Print("=== COMMENTARY DISPLAY DEBUG ===");
    Print("pa_commentary_count=", pa_commentary_count, ", start_index=", start_index, ", g_LatestCommentIndex=", g_LatestCommentIndex);

    // Loop from newest (highest index) to oldest (start_index) to display newest on top
    for(int i = pa_commentary_count - 1; i >= start_index; i--)
    {
        // Check if this is the latest trading context comment
        bool is_latest = (i == g_LatestCommentIndex);

        // DEBUG: Print first 3 and last 3 entries
        if(display_line < 3 || display_line > (pa_commentary_count - start_index - 4))
        {
            Print("Entry[", display_line, "]: i=", i, ", latest=", is_latest, ", ts=", TimeToString(price_action_commentary[i].timestamp), ", text=", StringSubstr(price_action_commentary[i].text, 0, 40));
        }

        // Get the text and check if it's a heading (contains emoji or all caps keywords)
        string text = price_action_commentary[i].text;
        bool is_heading = false;

        // Check if it's a heading (starts with emoji or contains patterns like "PRICE", "ORDER BLOCK", etc.)
        if(StringFind(text, "📍") >= 0 || StringFind(text, "🔊") >= 0 || StringFind(text, "🔇") >= 0 ||
           StringFind(text, "✓") >= 0 || StringFind(text, "⚡") >= 0 || StringFind(text, "🎯") >= 0 ||
           StringFind(text, "⛔") >= 0 || StringFind(text, "💥") >= 0 || StringFind(text, "📈") >= 0 ||
           StringFind(text, "📉") >= 0 || StringFind(text, "🚀") >= 0 || StringFind(text, "🔻") >= 0 ||
           StringFind(text, "⚠") >= 0 || StringFind(text, "🕯️") >= 0 || StringFind(text, "🟢") >= 0 ||
           StringFind(text, "🔴") >= 0 || StringFind(text, "⚖️") >= 0 || StringFind(text, "📊") >= 0 ||
           StringFind(text, "🐌") >= 0 || StringFind(text, "📦") >= 0 ||
           (StringFind(text, "PRICE") >= 0 && StringFind(text, "RANGE") >= 0) ||
           (StringFind(text, "ORDER BLOCK") >= 0) ||
           (StringFind(text, "FVG") >= 0 && StringFind(text, "FILLED") >= 0) ||
           (StringFind(text, "LIQUIDITY SWEPT") >= 0) ||
           (StringFind(text, "MARKET STRUCTURE") >= 0) ||
           (StringFind(text, "BREAK OF STRUCTURE") >= 0) ||
           (StringFind(text, "CHANGE OF CHARACTER") >= 0) ||
           (StringFind(text, "VOLUME") >= 0 && StringFind(text, "SPIKE") >= 0) ||
           (StringFind(text, "PIN BAR") >= 0) ||
           (StringFind(text, "ENGULFING") >= 0) ||
           (StringFind(text, "DOJI") >= 0) ||
           (StringFind(text, "TREND") >= 0) ||
           (StringFind(text, "MOMENTUM") >= 0) ||
           (StringFind(text, "VOLATILITY EXPANDING") >= 0) ||
           (StringFind(text, "CONSOLIDATION") >= 0) ||
           (StringFind(text, "BREAKOUT") >= 0) ||
           (StringFind(text, "BREAKDOWN") >= 0) ||
           (StringFind(text, "Testing EMA200") >= 0))
        {
            is_heading = true;
        }

        // Add timestamp for headings
        string display_text = text;
        if(is_heading && price_action_commentary[i].timestamp > 0)
        {
            string time_ago = FormatTimeDifference(price_action_commentary[i].timestamp);
            display_text = text + "  [" + time_ago + "]";
        }

        // Add arrow indicator to the LATEST comment (moves to newest)
        if(is_latest)
        {
            display_text = display_text + "  ◄◄◄ LATEST";  // Arrow points to newest comment
        }

        // Wrap text into multiple lines (400 chars per line for massive texts)
        string wrapped_lines[];
        WrapText(display_text, wrapped_lines, 400);

        // Display each wrapped line using OBJ_LABEL
        for(int line_idx = 0; line_idx < ArraySize(wrapped_lines); line_idx++)
        {
            string label_name = prefix + "PAC_" + IntegerToString(display_line);

            // Delete first to ensure clean recreation
            ObjectDelete(0, label_name);

            // Create fresh OBJ_LABEL
            ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
            ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
            ObjectSetInteger(0, label_name, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);

            // Indent continuation lines
            int indent = (line_idx > 0) ? 15 : 0;
            ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10 + indent);
            ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, y + 75 + display_line * line_height);

            // Use bold font for headings OR for the latest comment (first line only)
            if((is_heading || is_latest) && line_idx == 0)
                ObjectSetString(0, label_name, OBJPROP_FONT, "Arial Bold");
            else
                ObjectSetString(0, label_name, OBJPROP_FONT, "Consolas");

            ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, is_heading ? 10 : 9);
            ObjectSetString(0, label_name, OBJPROP_TEXT, wrapped_lines[line_idx]);

            // Use yellow color for the latest comment
            color display_color = price_action_commentary[i].text_color;
            if(is_latest)
            {
                display_color = clrYellow;  // Bright yellow for latest comment
            }

            ObjectSetInteger(0, label_name, OBJPROP_COLOR, display_color);

            display_line++;  // Move to next display line
        }
    }

    // Show info message if no commentary yet
    if(pa_commentary_count == 0)
    {
        string label_name = prefix + "PAC_0";
        ObjectCreate(0, label_name, OBJ_LABEL, 0, 0, 0);
        ObjectSetInteger(0, label_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
        ObjectSetString(0, label_name, OBJPROP_FONT, "Arial");
        ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 10);
        ObjectSetInteger(0, label_name, OBJPROP_XDISTANCE, x + 10);
        ObjectSetInteger(0, label_name, OBJPROP_YDISTANCE, y + 35);
        ObjectSetString(0, label_name, OBJPROP_TEXT, "Waiting for market activity...");
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, clrGray);
    }
}

//+------------------------------------------------------------------+