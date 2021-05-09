var button= document.getElementById("changecolor");

button.addEventListener('click',function ()
{
    console.log("ssss");
    Math.random();
    var r,g,b;
    r=Math.floor(Math.random() * 255);  
    g=Math.floor(Math.random() * 255);  
    b=Math.floor(Math.random() * 255);  
    var RGB_Vector=`rgb(${r},${g},${b})`;
    document.body.style.backgroundColor =  RGB_Vector;
})