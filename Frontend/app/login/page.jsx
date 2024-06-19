'use client';

import React, { useState } from "react";
import { Cookies } from "react-cookie";


const Login = () => {
  const [email, setEmail] = useState('');
  const cookies = new Cookies();

  const handleEmailChange = (event) => {
    setEmail(event.target.value);
  };

  const handelButton = () => {
    cookies.set('email',email);
  }

  return (
    <div>
      <h2>Login Page</h2>
      <form>
        <div>
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={handleEmailChange}
          />
        </div>
        <button onClick={handelButton} type="submit">Login</button>
      </form>
    </div>
  );
};

export default Login;
