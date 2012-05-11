-- ** ------------------------------------------------------------------- ** --
-- **
-- ** Navigation
-- **
-- ** Note that META is defined in cfg_ion.lua to control+alt
-- **
-- ** META + comma           = Switch to the tab to the left
-- ** META + period          = Switch to the tab to the right
-- **
-- ** META + left            = Switch to the frame to the left
-- ** META + right           = Switch to the frame to the right
-- ** META + up              = Switch to the frame to the up
-- ** META + down            = Switch to the frame to the down
-- **
-- ** META + k, comma        = Move this tab to the left
-- ** META + k, period       = Move this tab to the right
-- ** META + k, left         = Move this window to the frame on the left
-- ** META + k, right        = Move this window to the frame on the right
-- ** META + k, up           = Move this window to the frame above
-- ** META + k, down         = Move this window to the frame below 
-- **
-- ** META + Shift + up      = Move the workspace above
-- ** META + Shift + down    = Move the workspace below
-- **
-- ** Control + Tab          = Cycles through frames
-- ** Control + Shift + Tab  = Cycles through elements within a frame
-- **
-- ** ------------------------------------------------------------------- ** --
-- ** Other bindings documented listed here for convenience, though they 
-- ** are defined elsewhere:
-- **
-- ** Defined in cfg_ioncore.lua:
-- **
-- ** META + 1            = Move to the first workspace
-- ** META + 2            = Move to the second workspace
-- ** ... etc
-- **
-- ** Defined in emacs_bindings.lua:
-- **
-- ** META + x, 2         = Split the frame vertically
-- ** META + x, 3         = Split the frame horizontally
-- ** META + x, 0         = Get rid of this frame, collapse into the next one
-- ** META + x, 1         = Expand this frame, consuming all other frames.  
-- **
-- ** ------------------------------------------------------------------- ** --

-- Caution: these may break the default bindings.
UP="Up" ; DOWN="Down" ; LEFT="Left" ; RIGHT="Right"
-- UP="K" ; DOWN="J" ; LEFT="H" ; RIGHT="L"
-- UP="W" ; DOWN="S" ; LEFT="A" ; RIGHT="D"

defbindings("WFrame", {
    bdoc("Switch to the window to the left/right."),
    kpress(META.."comma",  "WFrame.switch_prev(_)", "_sub:non-nil"),
    kpress(META.."period", "WFrame.switch_next(_)", "_sub:non-nil"),
})

defbindings("WScreen", {
    bdoc("Switch to the frame to the left/right/above/below."),
    kpress(META..LEFT,    "ioncore.goto_next(_chld, 'left')"),
    kpress(META..RIGHT,   "ioncore.goto_next(_chld, 'right')"),
    kpress(META..UP,      "ioncore.goto_next(_chld, 'above')"),
    kpress(META..DOWN,    "ioncore.goto_next(_chld, 'below')"),
    -- Cycles through frams
    kpress("Tab+Control", "ioncore.goto_next(_chld, 'next')"),
})

-- WCY: 
--
-- I don't understand the bdoc below.  As far as I can tell, this
-- moves between workspaces.
defbindings("WScreen", {
    bdoc("Switch to next/previous object within current screen."),
    kpress(META.."Shift+"..UP,   "WScreen.switch_prev(_)"),
    kpress(META.."Shift+"..DOWN, "WScreen.switch_next(_)"),
})

-- Move current window in a frame to another frame in specified direction

move_current={}

function move_current.move(ws, dir)
    local frame=ws:current()
    local cwin=frame:current()
    local frame2=ioncore.navi_next(frame,dir)
    
    if frame2 then
        frame2:attach(cwin, { switchto=true })
    end
    cwin:goto()
end

defbindings("WTiling", {
    submap(META.."K", {
        kpress("Up",    function(ws) move_current.move(ws, "up") end),
        kpress("Down",  function(ws) move_current.move(ws, "down") end),
        kpress("Left",  function(ws) move_current.move(ws, "left") end),
        kpress("Right", function(ws) move_current.move(ws, "right") end),
    }),
})

-- Control shift tab cycles through elements in a frame
defbindings("WFrame", {
   bdoc("Switch to next/previous object within the frame."),
   kpress("Tab+Control+Shift", "WFrame.switch_next(_)"),
})

-- ** ------------------------------------------------------------------- ** --
-- ** Key Bindings
-- **
-- ** F2 = an xterm with color
-- ** ------------------------------------------------------------------- ** --

defbindings("WMPlex", {
    bdoc("Run a terminal emulator."),
    kpress(ALTMETA.."F2", "ioncore.exec_on(_, 'xterm -bg `/u/yuanc/bin/my_randcolor`')"),
})

-- ** ------------------------------------------------------------------- ** --
-- ** Menus
-- ** ------------------------------------------------------------------- ** --

-- Context menu (frame actions etc.)
defctxmenu("WFrame", "Frame", {

    -- Note: this propagates the close to any subwindows; it does not
    -- destroy the frame itself, unless empty. An entry to destroy tiled
    -- frames is configured in cfg_tiling.lua.
    menuentry("Close",          "WRegion.rqclose_propagate(_, _sub)"),

    --
    -- Other stuff could appear here, depending on the context
    -- 

    -- Low-priority entries will appear at the bottom of the menu.  
    menuentry("Attach tagged", "ioncore.tagged_attach(_)",     { priority = 0 }),
    menuentry("Clear tags",    "ioncore.tagged_clear()",       { priority = 0 }),
    menuentry("Window info",   "mod_query.show_tree(_, _sub)", { priority = 0 }),
    submenu("Styles",          "stylemenu",                    { priority = 0 }),
    submenu("Utilities",       "utilities",                    { priority = 0 }),
    submenu("Session",         "sessionmenu",                  { priority = 0 }),
})

defmenu("utilities", {
    menuentry("Color Xterm",   "ioncore.exec_on(_, 'xterm -bg `/u/yuanc/bin/my_randcolor`')"),
    menuentry("Emacs",         "ioncore.exec_on(_, 'emacs &')"),
})

