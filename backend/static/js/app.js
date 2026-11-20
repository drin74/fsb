(function () {
    "use strict";

    function tickClock() {
        var node = document.getElementById("clock");
        if (!node) return;
        var now = new Date();
        var pad = function (v) { return String(v).padStart(2, "0"); };
        node.textContent = pad(now.getHours()) + ":" + pad(now.getMinutes()) + ":" + pad(now.getSeconds());
    }

    function setupTabs() {
        var nav = document.querySelector("[data-tabs]");
        if (!nav) return;
        var buttons = Array.prototype.slice.call(nav.querySelectorAll("[data-tab]"));
        var panels = Array.prototype.slice.call(document.querySelectorAll("[data-panel]"));

        function activate(name, updateHash) {
            var found = false;
            buttons.forEach(function (btn) {
                var on = btn.getAttribute("data-tab") === name;
                btn.classList.toggle("is-active", on);
                if (on) found = true;
            });
            if (!found) return;
            panels.forEach(function (panel) {
                panel.classList.toggle("is-active", panel.getAttribute("data-panel") === name);
            });
            if (updateHash) {
                history.replaceState(null, "", "#" + name);
            }
        }

        buttons.forEach(function (btn) {
            btn.addEventListener("click", function () {
                activate(btn.getAttribute("data-tab"), true);
            });
        });

        if (window.location.hash) {
            activate(window.location.hash.slice(1), false);
        }

        window.addEventListener("hashchange", function () {
            activate(window.location.hash.slice(1), false);
        });
    }

    function fadeMessages() {
        var messages = document.querySelectorAll(".messages .message");
        if (!messages.length) return;
        setTimeout(function () {
            messages.forEach(function (node) {
                node.style.transition = "opacity .5s, transform .5s";
                node.style.opacity = "0";
                node.style.transform = "translateY(-4px)";
                setTimeout(function () { node.remove(); }, 600);
            });
        }, 6000);
    }

    document.addEventListener("DOMContentLoaded", function () {
        tickClock();
        setInterval(tickClock, 1000);
        setupTabs();
        fadeMessages();
    });
})();
