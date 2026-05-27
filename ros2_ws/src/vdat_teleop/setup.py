from setuptools import setup

package_name = "vdat_teleop"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Shubham Ghogare",
    maintainer_email="sghogare1498@gmail.com",
    description="Vision-based teleoperation publisher for robot arm control.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "webcam_teleop_node = vdat_teleop.webcam_teleop_node:main",
	        "virtual_ee_simulator_node = vdat_teleop.virtual_ee_simulator_node:main",
        ],
    },
)
