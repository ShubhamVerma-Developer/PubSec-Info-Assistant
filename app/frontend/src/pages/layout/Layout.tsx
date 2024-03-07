// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import { Outlet, NavLink, Link } from "react-router-dom";

import openai from "../../assets/openai.svg";
import { WarningBanner } from "../../components/WarningBanner/WarningBanner";
import styles from "./Layout.module.css";
import { Title } from "../../components/Title/Title";
import { ToggleContext } from '../../components/Title/Toggle';
import React from "react";
import Switch from 'react-switch';

const Layout = () => {
    // const { toggle, setToggle } = React.useContext(ToggleContext);

    // const handleToggle = () => {
    //     setToggle(prevToggle => prevToggle === 'Work' ? 'Web' : 'Work');
    // };
    const { toggle, setToggle } = React.useContext(ToggleContext);

    const handleToggle = () => {
        setToggle((prevToggle) => (prevToggle === 'Work' ? 'Web' : 'Work'));
    };
        return (
            <div className={styles.layout}>
                <header className={styles.header} role={"banner"}>
                    <WarningBanner />
                    <div className={styles.headerContainer}>
                        <div className={styles.headerTitleContainer}>
                            <img src={openai} alt="Azure OpenAI" className={styles.headerLogo} />
                            <h3 className={styles.headerTitle}><Title /></h3>
                        </div>
                        <nav>
                            <ul className={styles.headerNavList}>
                                <li>
                                    <NavLink to="/" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                        Chat
                                    </NavLink>
                                </li>
                                <li className={styles.headerNavLeftMargin}>
                                    <NavLink to="/content" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}>
                                        Manage Content
                                    </NavLink>
                                </li>
                            </ul>
                        </nav>
                    </div>
                </header>
                <div className={styles.raibanner}>
                    <div></div>
                    <div className={styles.centered}>
                        <span className={styles.raiwarning}>AI-generated content may be incorrect</span>
                    </div>
                    <div className={styles.right}>
                        <Switch
                            onChange={handleToggle}
                            checked={toggle === 'Web'}
                            uncheckedIcon={false}
                            checkedIcon={false}
                            onColor="#86d3ff"
                            offColor="#ccc"
                        />
                        <label onClick={handleToggle} style={{ marginLeft: '10px', cursor: 'pointer' }}>
                            {toggle === 'Work' ? 'Switch to Web' : 'Switch to Work'}
                        </label>
                    </div>
                </div>

                <Outlet />

                <footer>
                    <WarningBanner />
                </footer>
            </div>
        );
    };

    export default Layout;
