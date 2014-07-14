-- ** ------------------------------------------------------------------- ** --
-- **
-- ** Reminder (also mentioned in ion3_instructions.txt):
-- **
-- ** If you are looking for things which aren't defined here, look in:
-- **  ION_ROOT/*/*.lua
-- **  ~/.ion3
-- **  ~/.ion3/lib
-- **
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
-- ** META + k, comma     = Move this tab to the left
-- ** META + k, period    = Move this tab to the right
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
-- ** Not sure where these are defined:
-- **
-- ** META + t            = Tag a window
-- ** META + k, a         - Move all tagged windows to this frame
-- **
-- ** F1  - man page
-- ** F2  - start a new xterm (defined below)
-- ** F3  - run a command
-- ** F4  - ssh to
-- ** F5  - edit file
-- ** F6  - view file
-- ** F7  - undefined
-- ** F8  - not sure, it's captured by vnc
-- ** F9  - create a new workspace
-- ** F10 - undefined
-- ** F11 - undefined
-- ** F12 - menu
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

defbindings("WMPlex.toplevel", {
    bdoc("Free up the f9 key so I can try to remap it to insert"),
    kpress(ALTMETA.."F9", nil),
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

-- There is a known problem with the FLTK library used by TigerVNC Viewer
-- that means that control+alt+normal-charcter-key doesn't get sent.
-- control+alt+function-key does work.
--
-- So I'm adding:
--

-- ** META + Page_Up         = Switch to the tab to the left
-- ** META + Page_Down       = Switch to the tab to the right
-- **
-- ** META + Home, left      = Move this window to the frame on the left
-- ** META + Home, right     = Move this window to the frame on the right
-- ** META + Home, up        = Move this window to the frame above
-- ** META + Home, down      = Move this window to the frame below
-- ** META + Home, Page_Up   = Move this tab to the left
-- ** META + Home, Page_Down = Move this tab to the right
-- **
-- ** META + End, 2      = Split the frame vertically
-- ** META + End, 3      = Split the frame horizontally
-- ** META + End, 0      = Get rid of this frame, collapse into the next one
-- ** META + End, 1      = Expand this frame, consuming all other frames.


defbindings("WFrame", {
    bdoc("Switch to the window to the left/right."),
    kpress(META.."Page_Up",  "WFrame.switch_prev(_)", "_sub:non-nil"),
    kpress(META.."Page_Down",  "WFrame.switch_next(_)", "_sub:non-nil"),
})

defbindings("WTiling", {
    submap(META.."Home", {
        kpress("Up",    function(ws) move_current.move(ws, "up") end),
        kpress("Down",  function(ws) move_current.move(ws, "down") end),
        kpress("Left",  function(ws) move_current.move(ws, "left") end),
        kpress("Right", function(ws) move_current.move(ws, "right") end),
    }),
})

defbindings("WFrame.toplevel", {
    submap(META.."Home", {
        bdoc("Move current object within the frame left/right."),
        kpress("Page_Up",   "WFrame.dec_index(_, _sub)", "_sub:non-nil"),
        kpress("Page_Down", "WFrame.inc_index(_, _sub)", "_sub:non-nil"),
    }),
})

-- this one doesn't seem to work
Emacs.WTiling = {
    submap(META.."Shift+Page_Up", {
        bdoc("Destroy current frame."),
        kpress ("AnyModifier+0", "WTiling.unsplit_at(_, _sub)"),

        bdoc("Move all windows on WTiling to single frame and destroy rest"),
        kpress ("AnyModifier+1", "collapse.collapse(_)"),

        bdoc("Split current frame vertically"),
        kpress ("AnyModifier+2", "WTiling.split_at(_, _sub, 'top', true)"),

        bdoc("Split current frame horizontally"),
        kpress ("AnyModifier+3", "WTiling.split_at(_, _sub, 'left', true)"),

        submap(META.."Down", {
            bdoc("Split current floating frame vertically"),
            kpress("AnyModifier+2",
 	          "WTiling.split_at(_, _sub, 'floating:bottom', true)"),

	    bdoc("Split current floating frame horizontally"),
            kpress("AnyModifier+3",
                  "WTiling.split_at(_, _sub, 'floating:right', true)"),
         }),

        bdoc("Cycle to the next workspace"),
        kpress ("AnyModifier+o", "WTiling.other_client(_, _sub)")
    }),
}


-- ** ------------------------------------------------------------------- ** --
--
-- Attempt to use F keys, since Mac keyboards usually don't have
-- insert, delete, home, end, page up, page down.
--
-- But this doesn't seem to work...
--

-- ** META + F4         = Switch to the tab to the left
-- ** META + F5         = Switch to the tab to the right
-- **
-- ** META + F1, left   = Move this window to the frame on the left
-- ** META + F1, right  = Move this window to the frame on the right
-- ** META + F1, up     = Move this window to the frame above
-- ** META + F1, down   = Move this window to the frame below
-- ** META + F2, left   = Move this tab to the left
-- ** META + F2, right  = Move this tab to the right
-- **
-- ** META + F3, 2      = Split the frame vertically
-- ** META + F3, 3      = Split the frame horizontally
-- ** META + F3, 0      = Get rid of this frame, collapse into the next one
-- ** META + F3, 1      = Expand this frame, consuming all other frames.


defbindings("WFrame", {
    bdoc("Switch to the window to the left/right."),
    kpress(META.."F4",  "WFrame.switch_prev(_)", "_sub:non-nil"),
    kpress(META.."F5",  "WFrame.switch_next(_)", "_sub:non-nil"),
})

defbindings("WTiling", {
    submap(META.."F1", {
        kpress("Up",    function(ws) move_current.move(ws, "up") end),
        kpress("Down",  function(ws) move_current.move(ws, "down") end),
        kpress("Left",  function(ws) move_current.move(ws, "left") end),
        kpress("Right", function(ws) move_current.move(ws, "right") end),
    }),
})

defbindings("WFrame.toplevel", {
    submap(META.."F2", {
        bdoc("Move current object within the frame left/right."),
        kpress("Left",   "WFrame.dec_index(_, _sub)", "_sub:non-nil"),
        kpress("Right", "WFrame.inc_index(_, _sub)", "_sub:non-nil"),
    }),
})

Emacs.WTiling = {
    submap(META.."F3", {
        bdoc("Destroy current frame."),
        kpress ("AnyModifier+0", "WTiling.unsplit_at(_, _sub)"),

        bdoc("Move all windows on WTiling to single frame and destroy rest"),
        kpress ("AnyModifier+1", "collapse.collapse(_)"),

        bdoc("Split current frame vertically"),
        kpress ("AnyModifier+2", "WTiling.split_at(_, _sub, 'top', true)"),

        bdoc("Split current frame horizontally"),
        kpress ("AnyModifier+3", "WTiling.split_at(_, _sub, 'left', true)"),

        submap(META.."Down", {
            bdoc("Split current floating frame vertically"),
            kpress("AnyModifier+2",
 	          "WTiling.split_at(_, _sub, 'floating:bottom', true)"),

	    bdoc("Split current floating frame horizontally"),
            kpress("AnyModifier+3",
                  "WTiling.split_at(_, _sub, 'floating:right', true)"),
         }),

        bdoc("Cycle to the next workspace"),
        kpress ("AnyModifier+o", "WTiling.other_client(_, _sub)")
    }),
}

-- ** ------------------------------------------------------------------- ** --
-- ** Change XTERM to have color and run bash
-- ** ------------------------------------------------------------------- ** --

--defbindings("WMPlex.toplevel", {
--    bdoc("Run a terminal emulator."),
--    kpress(ALTMETA.."F2", "ioncore.exec_on(_, 'xterm -bg `/u/yuanc/bin/my_randcolor`')"),
--})

XTERM="xterm -bg `/u/yuanc/bin/my_randcolor` -fg black -e bash"

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
    menuentry("Color Xterm",   "ioncore.exec_on(_, XTERM)"),
    menuentry("Emacs",         "ioncore.exec_on(_, 'emacs &')"),
})

