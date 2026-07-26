window.addEventListener("scroll",()=>{

document.querySelectorAll(".fade-up").forEach(el=>{

const top=el.getBoundingClientRect().top;

if(top<window.innerHeight-80){

el.classList.add("show");

}

});

});
