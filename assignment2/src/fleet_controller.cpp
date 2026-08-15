#include "assignment2/Robot.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include <map>
#include <string>

class FleetControllerNode : public rclcpp::Node {
private:

    std::map<std::string, RobotPlatform*> fleet_;
    rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr mission_sub_;

public:
    FleetControllerNode() : Node("fleet_controller_node") {
        
        AudiCar *my_audi = new AudiCar("audi", this);
        fleet_["audi"] = my_audi;
        
        // Add the Husky to the fleet
        HuskyRobot *my_husky = new HuskyRobot("husky", this);
        fleet_["husky"] = my_husky;
        
        RCLCPP_INFO(this->get_logger(), "Fleet Controller has opened...");

        mission_sub_ = this->create_subscription<geometry_msgs::msg::PoseStamped>(
            "/mission/target", 10,
            std::bind(&FleetControllerNode::missionCallback, this, std::placeholders::_1)
        );
    }

    ~FleetControllerNode() {
        std::map<std::string, RobotPlatform*>::iterator it;
        for (it = fleet_.begin(); it != fleet_.end(); ++it) {
            delete it->second;
        }
    }

private:
    void missionCallback(const geometry_msgs::msg::PoseStamped::SharedPtr msg) {
        
        std::string target_id = msg->header.frame_id; 
        
        std::map<std::string, RobotPlatform*>::iterator it = fleet_.find(target_id);
        
        if (it != fleet_.end()) {
            RobotPlatform* found_robot = it->second;
            found_robot->addGoal(msg->pose.position);
        } else {
            RCLCPP_WARN(this->get_logger(), "Unknown fleet");
        }
    }
};

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<FleetControllerNode>());
    rclcpp::shutdown();
    return 0;
}