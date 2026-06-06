const burger =
document.getElementById(
"burger"
);

const nav =
document.getElementById(
"navLinks"
);

if(burger){

burger.addEventListener(
"click",
()=>{

nav.classList.toggle(
"active"
);

});
}

/* CLOSE MENU AFTER CLICK */

const links =
document.querySelectorAll(
".nav-links a"
);

links.forEach(link=>{

link.addEventListener(
"click",
()=>{

nav.classList.remove(
"active"
);

});

});

/* AI SCANNER */

const form =
document.getElementById(
"uploadForm"
);

if(form){

form.addEventListener(
"submit",
()=>{

const btn =
form.querySelector(
"button"
);

btn.innerText =
"AI Scanning...";

btn.disabled = true;

});

}
