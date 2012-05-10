-- ** ------------------------------------------------------------------- ** --
-- ** 
-- ** Navigation
-- ** 
-- ** Note that META is defined in cfg_ion.lua to control+alt
-- ** 
-- ** META + comma        = Switch to the tab to the left
-- ** META + period       = Switch to the tab to the right
-- **
-- ** META + left         = Switch to the frame to the left
-- ** META + right        = Switch to the frame to the right
-- ** META + up           = Switch to the frame to the up
-- ** META + down         = Switch to the frame to the down
-- ** 
-- ** META + k, comma    = Move this tab to the left
-- ** META + k, period   = Move this tab to the right
-- ** META + k, left     = Move this window to the frame on the left
-- ** META + k, right    = Move this window to the frame on the right
-- ** META + k, up       = Move this window to the frame above
-- ** META + k, down     = Move this window to the frame below 
-- **
-- ** META + Shift + up   = Move the workspace above
-- ** META + Shift + down = Move the workspace below
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
    -- moves to the window to the left
    kpress(META.."comma", "WFrame.switch_prev(_)", "_sub:non-nil"),
    -- moves to the window to the right
    kpress(META.."period", "WFrame.switch_next(_)", "_sub:non-nil"),
})

defbindings("WScreen", {
    bdoc("Switch to the frame to the left/right."),
    -- moves to the frame to the left
    kpress(META..LEFT, "ioncore.goto_next(_chld, 'left')"),
    -- moves to the frame to the right
    kpress(META..RIGHT, "ioncore.goto_next(_chld, 'right')"),
    kpress(META..UP, "ioncore.goto_next(_chld, 'above')"),
    kpress(META..DOWN, "ioncore.goto_next(_chld, 'below')"),
})

-- WCY: 
-- I don't understand the bdoc below.  As far as I can tell, this moves between workspaces.  
defbindings("WScreen", {
    bdoc("Switch to next/previous object within current screen."),
    kpress(META.."Shift+"..UP, "WScreen.switch_prev(_)"),
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
        kpress("Up", function(ws) move_current.move(ws, "up") end),
        kpress("Down", function(ws) move_current.move(ws, "down") end),
        kpress("Left", function(ws) move_current.move(ws, "left") end),
        kpress("Right", function(ws) move_current.move(ws, "right") end),
    }),
})

-- ** ------------------------------------------------------------------- ** --
-- ** 
-- ** ------------------------------------------------------------------- ** --
