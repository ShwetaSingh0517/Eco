function aleartfunc(){
    if (confirm("Do you want to submit") == true) {
        alert("You have submited")
      } else {
        alert("Please submit the form ")
      }
}


function datavalue(){
  var name = document.getElementById("name").value;
  var sname = document.getElementById("Sur-Name").value;
  var dob = document.getElementById("dob").value;
  var add = document.getElementById("add").value;
  var phone = document.getElementById("phone").value;
  var email = document.getElementById("email").value;
  var SId = document.getElementById("Student-Id").value;
  var year = document.getElementById("year").value;
  var branch = document.getElementById("branch").value;
  var sports = document.getElementById("sports").value;
document.writeln("Your info: <br>"+"Name:"+name+"<br>")
document.writeln("Sur-Name:"+sname+"<br>")
document.writeln("DOB:"+dob+"<br>")
document.writeln("Address:"+add+"<br>")
document.writeln("Phone No:"+phone+"<br>")
document.writeln("Email:"+email+"<br>")
document.writeln("Student Id:"+SId+"<br>")
document.writeln("year:"+year+"<br>")
document.writeln("Branch:"+branch+"<br>")
document.writeln("Sports:"+sports+"<br>")
}
